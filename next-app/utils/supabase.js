import { createClient } from '@supabase/supabase-js';

// Initialize the Supabase client with environment variables
// These should be set in .env.local for local development
// and in Vercel environment variables for production
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// Create a singleton instance of the Supabase client
let supabase = null;

// Function to get or create the Supabase client
export const getSupabase = () => {
  // If client already exists, return it (singleton pattern)
  if (supabase) {
    return supabase;
  }

  // Validate environment variables
  if (!supabaseUrl || !supabaseKey) {
    console.error('Missing Supabase environment variables. Check .env.local file.');
    // Return a dummy client in development to prevent crashes
    if (process.env.NODE_ENV === 'development') {
      return {
        from: () => ({
          select: () => ({ data: null, error: new Error('Supabase configuration missing') }),
          insert: () => ({ data: null, error: new Error('Supabase configuration missing') }),
          update: () => ({ data: null, error: new Error('Supabase configuration missing') }),
          delete: () => ({ data: null, error: new Error('Supabase configuration missing') }),
        }),
        auth: {
          signIn: () => Promise.reject(new Error('Supabase configuration missing')),
          signUp: () => Promise.reject(new Error('Supabase configuration missing')),
          signOut: () => Promise.reject(new Error('Supabase configuration missing')),
        },
      };
    }
    // In production, throw an error
    throw new Error('Supabase client could not be created. Environment variables missing.');
  }

  // Create the client
  supabase = createClient(supabaseUrl, supabaseKey);
  return supabase;
};

// Database operations

/**
 * Fetch recent candlestick data from Supabase
 * @param {string} instrument - Trading pair (e.g., "XAU_USD")
 * @param {string} granularity - Time interval (e.g., "H1")
 * @param {number} limit - Maximum number of records to return
 * @returns {Promise<{data: Array, error: Error}>} - Supabase response
 */
export const getRecentCandles = async (instrument = 'XAU_USD', granularity = 'H1', limit = 100) => {
  const supabase = getSupabase();
  
  return supabase
    .from('candlesticks')
    .select('*')
    .eq('instrument', instrument)
    .eq('granularity', granularity)
    .order('timestamp', { ascending: false })
    .limit(limit);
};

/**
 * Save user feedback to Supabase
 * @param {Object} feedback - Feedback data
 * @param {string} feedback.model - AI model used
 * @param {number} feedback.rating - User rating (1-5)
 * @param {string} feedback.comments - User comments
 * @param {string} feedback.analysisId - ID of the analysis
 * @returns {Promise<{data: Object, error: Error}>} - Supabase response
 */
export const saveFeedback = async (feedback) => {
  const supabase = getSupabase();
  
  return supabase
    .from('feedback')
    .insert([
      {
        model: feedback.model,
        rating: feedback.rating,
        comments: feedback.comments,
        analysis_id: feedback.analysisId,
        created_at: new Date().toISOString()
      }
    ]);
};

export default getSupabase;
