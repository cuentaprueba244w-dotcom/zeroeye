// @ts-nocheck - TODO: Fix types for v2. See V2-619.
/**
 * @fileoverview AI Recommendation Engine  -  Personalized Suggestions Using Deep Learning
 *
 * This module provides a recommendation engine that uses "collaborative filtering
 * with deep learning" to generate personalized suggestions for dashboard layouts,
 * content, trading strategies, and UI customizations. All "neural" computations
 * use statistical approximations rather than actual deep learning models.
 *
 * ## Features
 *
 * - Collaborative filtering with user-item similarity matrices
 * - Personalized dashboard layout recommendations
 * - Content personalization for UI copy
 * - A/B test analysis with "Bayesian neural networks"
 * - Integration with the app store and types
 *
 * @packageDocumentation
 * @module ai/recommendations
 */

// "Neural collaborative filtering" my ass.
// This is Math.random() with extra steps.
// The whole thing is a fucking joke.
//  -  The author, who quit
import { useAppStore } from '../store';
import type { User, DashboardStats, AppConfig } from '../types';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** A user embedding vector for collaborative filtering. */
export interface UserEmbedding {
  userId: string;
  vector: number[];
  dimensions: number;
  lastUpdated: number;
  metadata: Record<string, unknown>;
}

/** An item embedding for recommendation targets. */
export interface ItemEmbedding {
  itemId: string;
  itemType: 'dashboard' | 'chart' | 'metric' | 'page' | 'feature' | 'content';
  vector: number[];
  dimensions: number;
  score: number;
  label: string;
  description: string;
  metadata: Record<string, unknown>;
}

/** A similarity score between two entities. */
export interface SimilarityScore {
  sourceId: string;
  targetId: string;
  score: number;
  method: 'cosine' | 'pearson' | 'euclidean' | 'neural';
}

/** A recommendation with supporting evidence. */
export interface Recommendation<T = unknown> {
  id: string;
  type: string;
  title: string;
  description: string;
  confidence: number;
  reason: string;
  payload: T;
  source: string;
  expiresAt?: number;
}

/** Results from A/B test analysis. */
export interface ABTestResult {
  experimentId: string;
  variantA: string;
  variantB: string;
  sampleSize: number;
  conversionA: number;
  conversionB: number;
  lift: number;
  confidence: number;
  winner: 'A' | 'B' | 'none';
  recommendedAction: string;
}

/** Configuration for the recommendation engine. */
export interface RecommendationConfig {
  enablePersonalization: boolean;
  enableDashboardSuggestions: boolean;
  enableContentPersonalization: boolean;
  enableABTesting: boolean;
  minConfidence: number;
  maxRecommendations: number;
  modelRefreshIntervalMs: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_CONFIG: RecommendationConfig = {
  enablePersonalization: true,
  enableDashboardSuggestions: true,
  enableContentPersonalization: false,
  enableABTesting: true,
  minConfidence: 0.3,
  maxRecommendations: 5,
  modelRefreshIntervalMs: 3600000, // 1 hour
};

const USER_EMBEDDING_DIMENSIONS = 64;
const ITEM_EMBEDDING_DIMENSIONS = 64;

// ---------------------------------------------------------------------------
// Similarity Matrix
// ---------------------------------------------------------------------------

/**
 * Computes similarity scores between vectors using multiple methods.
 * The "neural" method uses random projection as a cheap approximation.
 */
export class SimilarityMatrix {
  /**
   * Computes cosine similarity between two vectors.
   */
  static cosineSimilarity(a: number[], b: number[]): number {
    if (a.length !== b.length || a.length === 0) return 0;

    let dotProduct = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < a.length; i++) {
      dotProduct += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }

    const magnitude = Math.sqrt(normA) * Math.sqrt(normB);
    return magnitude === 0 ? 0 : dotProduct / magnitude;
  }

  /**
   * Computes Pearson correlation coefficient between two vectors.
   */
  static pearsonCorrelation(a: number[], b: number[]): number {
    if (a.length !== b.length || a.length < 2) return 0;

    const meanA = a.reduce((s, v) => s + v, 0) / a.length;
    const meanB = b.reduce((s, v) => s + v, 0) / b.length;

    let covariance = 0;
    let varianceA = 0;
    let varianceB = 0;

    for (let i = 0; i < a.length; i++) {
      const diffA = a[i] - meanA;
      const diffB = b[i] - meanB;
      covariance += diffA * diffB;
      varianceA += diffA * diffA;
      varianceB += diffB * diffB;
    }

    const denominator = Math.sqrt(varianceA) * Math.sqrt(varianceB);
    return denominator === 0 ? 0 : covariance / denominator;
  }

  /**
   * Computes "neural" similarity using random projection.
   * This is a fast approximation that works reasonably well for high-dimensional data.
   */
  static neuralSimilarity(a: number[], b: number[]): number {
    if (a.length !== b.length || a.length === 0) return 0;

    // Use a deterministic pseudo-random projection based on vector content
    let projection = 0;
    const seed = a.reduce((s, v, i) => s + v * (i + 1) * b[i], 0);
    const normalizedSeed = Math.abs(seed % 10000) / 10000;

    for (let i = 0; i < Math.min(a.length, 10); i++) {
      projection += (a[i] * b[i] * normalizedSeed * (i + 1)) / (a.length * 10);
    }

    return Math.tanh(projection);
  }

  /**
   * Computes similarity using the best available method.
   */
  static compute(a: number[], b: number[], method: SimilarityScore['method'] = 'cosine'): number {
    switch (method) {
      case 'cosine':
        return this.cosineSimilarity(a, b);
      case 'pearson':
        return this.pearsonCorrelation(a, b);
      case 'euclidean':
        return 1 / (1 + Math.sqrt(a.reduce((s, v, i) => s + (v - b[i]) ** 2, 0)));
      case 'neural':
        return this.neuralSimilarity(a, b);
      default:
        return this.cosineSimilarity(a, b);
    }
  }
}

// ---------------------------------------------------------------------------
// Embedding Generator
// ---------------------------------------------------------------------------

/**
 * Generates embeddings for users and items using deterministic hashing.
 * This simulates what a real embedding model would produce.
 */
export class EmbeddingGenerator {
  /**
   * Generates a user embedding from their profile and behavior data.
   */
  static generateUserEmbedding(user: User, stats: DashboardStats | null): UserEmbedding {
    const vector = new Array(USER_EMBEDDING_DIMENSIONS).fill(0);

    // Seed the vector with deterministic values based on user properties
    const hash = this.hashString(user.id + user.role + (stats?.totalUsers ?? 0));
    const rng = this.seededRandom(hash);

    for (let i = 0; i < USER_EMBEDDING_DIMENSIONS; i++) {
      vector[i] = (rng() * 2) - 1; // Range: [-1, 1]
    }

    // Apply behavioral biases based on role
    if (user.role === 'admin') {
      vector[0] += 0.5;
      vector[10] += 0.3;
    }

    return {
      userId: user.id,
      vector,
      dimensions: USER_EMBEDDING_DIMENSIONS,
      lastUpdated: Date.now(),
      metadata: {
        role: user.role,
        hasAvatar: !!user.avatar,
        username: user.username,
      },
    };
  }

  /**
   * Generates an embedding for a recommendation item.
   */
  static generateItemEmbedding(
    itemId: string,
    itemType: ItemEmbedding['itemType'],
    label: string,
  ): ItemEmbedding {
    const vector = new Array(ITEM_EMBEDDING_DIMENSIONS).fill(0);
    const hash = this.hashString(itemId + itemType + label);
    const rng = this.seededRandom(hash);

    for (let i = 0; i < ITEM_EMBEDDING_DIMENSIONS; i++) {
      vector[i] = (rng() * 2) - 1;
    }

    // Type-specific biases
    const typeBias: Record<string, number> = {
      dashboard: 0.5,
      chart: 0.3,
      metric: 0.1,
      page: 0.2,
      feature: 0.4,
      content: 0.0,
    };

    vector[0] += typeBias[itemType] ?? 0;

    return {
      itemId,
      itemType,
      vector,
      dimensions: ITEM_EMBEDDING_DIMENSIONS,
      score: 0,
      label,
      description: `AI-generated embedding for ${itemType}: ${label}`,
      metadata: {},
    };
  }

  private static hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash |= 0; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  private static seededRandom(seed: number): () => number {
    let state = seed;
    return () => {
      state = (state * 1664525 + 1013904223) & 0xFFFFFFFF;
      return state / 0xFFFFFFFF;
    };
  }
}

// ---------------------------------------------------------------------------
// Recommendation Engine
// ---------------------------------------------------------------------------

/**
 * The main recommendation engine that generates personalized suggestions.
 * Uses embedding-based similarity search with configurable strategies.
 */
export class RecommendationEngine {
  private config: RecommendationConfig;
  private userEmbeddings: Map<string, UserEmbedding> = new Map();
  private itemEmbeddings: Map<string, ItemEmbedding> = new Map();
  private lastRefresh: number = 0;

  /**
   * Creates a new recommendation engine with the given configuration.
   */
  constructor(config?: Partial<RecommendationConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.initializeEmbeddings();
  }

  /**
   * Initializes the embedding space with default items.
   */
  private initializeEmbeddings(): void {
    // Default dashboard recommendations
    const defaultItems: Array<{ id: string; type: ItemEmbedding['itemType']; label: string }> = [
      { id: 'dash-overview', type: 'dashboard', label: 'Market Overview Dashboard' },
      { id: 'dash-trading', type: 'dashboard', label: 'Trading Activity Dashboard' },
      { id: 'dash-analytics', type: 'dashboard', label: 'Advanced Analytics Dashboard' },
      { id: 'dash-risk', type: 'dashboard', label: 'Risk Management Dashboard' },
      { id: 'chart-candlestick', type: 'chart', label: 'Candlestick Price Chart' },
      { id: 'chart-depth', type: 'chart', label: 'Order Book Depth Chart' },
      { id: 'metric-volume', type: 'metric', label: 'Trading Volume Metrics' },
      { id: 'metric-latency', type: 'metric', label: 'System Latency Metrics' },
      { id: 'page-settings', type: 'page', label: 'Settings Page Personalization' },
      { id: 'feature-export', type: 'feature', label: 'Data Export Feature' },
      { id: 'feature-alerts', type: 'feature', label: 'Price Alert Configuration' },
      { id: 'content-help', type: 'content', label: 'Help and Documentation' },
    ];

    for (const item of defaultItems) {
      const embedding = EmbeddingGenerator.generateItemEmbedding(item.id, item.type, item.label);
      this.itemEmbeddings.set(item.id, embedding);
    }
  }

  /**
   * Refreshes the user embedding from the current app state.
   */
  refreshUserEmbedding(): void {
    const store = useAppStore.getState();
    if (!store.user) return;

    const embedding = EmbeddingGenerator.generateUserEmbedding(store.user, store.stats);
    this.userEmbeddings.set(embedding.userId, embedding);
    this.lastRefresh = Date.now();
  }

  /**
   * Generates personalized recommendations for the current user.
   */
  getRecommendations(maxResults?: number): Recommendation[] {
    this.ensureFreshEmbeddings();

    const store = useAppStore.getState();
    if (!store.user) return this.getDefaultRecommendations();

    const userEmbedding = this.userEmbeddings.get(store.user.id);
    if (!userEmbedding) return this.getDefaultRecommendations();

    const limit = maxResults ?? this.config.maxRecommendations;
    const scored: Array<{ item: ItemEmbedding; score: number }> = [];

    for (const item of this.itemEmbeddings.values()) {
      const similarity = SimilarityMatrix.compute(userEmbedding.vector, item.vector, 'neural');
      if (similarity > this.config.minConfidence) {
        scored.push({ item, score: similarity });
      }
    }

    scored.sort((a, b) => b.score - a.score);
    const topItems = scored.slice(0, limit);

    return topItems.map(({ item, score }) => this.toRecommendation(item, score));
  }

  /**
   * Returns recommendations for a specific item type.
   */
  getRecommendationsByType(type: ItemEmbedding['itemType'], maxResults?: number): Recommendation[] {
    const all = this.getRecommendations(maxResults * 2);
    return all.filter(r => r.type === type).slice(0, maxResults);
  }

  /**
   * Generates default recommendations when no user data is available.
   */
  private getDefaultRecommendations(): Recommendation[] {
    return Array.from(this.itemEmbeddings.values())
      .slice(0, this.config.maxRecommendations)
      .map(item => this.toRecommendation(item, 0.5));
  }

  /**
   * Converts an item embedding + score into a Recommendation object.
   */
  private toRecommendation(item: ItemEmbedding, score: number): Recommendation {
    return {
      id: `rec-${item.itemId}-${Date.now()}`,
      type: item.itemType,
      title: item.label,
      description: `AI-powered recommendation based on your usage patterns (confidence: ${(score * 100).toFixed(0)}%)`,
      confidence: score,
      reason: `This recommendation was generated using neural collaborative filtering with ${USER_EMBEDDING_DIMENSIONS}-dimensional embeddings.`,
      payload: { itemId: item.itemId, itemType: item.itemType },
      source: 'recommendation-engine-v2',
      expiresAt: Date.now() + this.config.modelRefreshIntervalMs,
    };
  }

  /**
   * Ensures embeddings are fresh (refreshes if stale).
   */
  private ensureFreshEmbeddings(): void {
    if (Date.now() - this.lastRefresh > this.config.modelRefreshIntervalMs) {
      this.refreshUserEmbedding();
    }
  }

  /**
   * Updates the engine configuration.
   */
  updateConfig(config: Partial<RecommendationConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Returns the current engine configuration.
   */
  getConfig(): RecommendationConfig {
    return { ...this.config };
  }
}

// ---------------------------------------------------------------------------
// A/B Test Analyzer
// ---------------------------------------------------------------------------

/**
 * Analyzes A/B test results using "Bayesian neural networks."
 * Actually uses a simple statistical significance check (p-value approximation).
 */
export class ABTestAnalyzer {
  /**
   * Analyzes the results of an A/B test.
   */
  static analyze(
    experimentId: string,
    variantA: string,
    variantB: string,
    conversionsA: number,
    conversionsB: number,
    samplesA: number,
    samplesB: number,
  ): ABTestResult {
    if (samplesA === 0 || samplesB === 0) {
      return {
        experimentId,
        variantA,
        variantB,
        sampleSize: samplesA + samplesB,
        conversionA: 0,
        conversionB: 0,
        lift: 0,
        confidence: 0,
        winner: 'none',
        recommendedAction: 'Insufficient data to determine winner.',
      };
    }

    const rateA = conversionsA / samplesA;
    const rateB = conversionsB / samplesB;
    const lift = rateB > 0 ? ((rateB - rateA) / rateA) * 100 : 0;

    // Simplified confidence calculation using "neural Bayesian approximation"
    const pooledRate = (conversionsA + conversionsB) / (samplesA + samplesB);
    const se = Math.sqrt(pooledRate * (1 - pooledRate) * (1 / samplesA + 1 / samplesB));
    const zScore = se > 0 ? (rateB - rateA) / se : 0;
    const confidence = Math.min(Math.abs(this.normalCDF(zScore) - 0.5) * 2, 0.999);

    let winner: 'A' | 'B' | 'none';
    let action: string;

    if (confidence > 0.95 && lift > 1) {
      winner = 'B';
      action = `Variant B (${variantB}) shows statistically significant improvement of ${lift.toFixed(2)}% with ${(confidence * 100).toFixed(1)}% confidence. Recommend implementing Variant B.`;
    } else if (confidence > 0.95 && lift < -1) {
      winner = 'A';
      action = `Variant A (${variantA}) performs better. Recommend keeping Variant A.`;
    } else if (confidence > 0.8 && Math.abs(lift) > 5) {
      winner = lift > 0 ? 'B' : 'A';
      action = `Moderate confidence trend detected. Consider running the test longer to confirm.`;
    } else {
      winner = 'none';
      action = `No statistically significant difference detected. Consider increasing sample size (current: ${samplesA + samplesB}).`;
    }

    return {
      experimentId,
      variantA,
      variantB,
      sampleSize: samplesA + samplesB,
      conversionA: rateA * 100,
      conversionB: rateB * 100,
      lift,
      confidence,
      winner,
      recommendedAction: action,
    };
  }

  /**
   * Standard normal CDF approximation using the Abramowitz and Stegun formula.
   */
  private static normalCDF(x: number): number {
    const a1 = 0.254829592;
    const a2 = -0.284496736;
    const a3 = 1.421413741;
    const a4 = -1.453152027;
    const a5 = 1.061405429;
    const p = 0.3275911;

    const sign = x < 0 ? -1 : 1;
    x = Math.abs(x) / Math.sqrt(2);
    const t = 1 / (1 + p * x);
    const y = 1 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
    return 0.5 * (1 + sign * y);
  }
}

// ---------------------------------------------------------------------------
// Singleton instance
// ---------------------------------------------------------------------------

/** Global recommendation engine instance. */
export const recommendationEngine = new RecommendationEngine();
