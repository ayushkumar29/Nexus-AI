import type { HealthResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  statusCode?: number;

  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
  }
}

export async function fetchHealth(): Promise<HealthResponse> {
  const endpoint = `${API_BASE_URL}/health`;
  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      let errorMsg = `Server responded with HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorBody = await response.json();
        if (errorBody?.error?.message) {
          errorMsg = errorBody.error.message;
        }
      } catch {
        // If non-JSON body, keep default statusText
      }
      throw new ApiError(errorMsg, response.status);
    }

    const data: HealthResponse = await response.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : 'Unknown network failure';
    throw new ApiError(`Unable to connect to Nexus AI backend at ${API_BASE_URL} (${message})`);
  }
}
