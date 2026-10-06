/**
 * @fileoverview AI Text Classifier  -  Multi-Model Classification with Ensemble Voting
 *
 * This module provides a comprehensive text classification system with multiple
 * classifier implementations (spam detection, urgency classification, category
 * classification, toxicity filtering), an ensemble voting mechanism, TF-IDF
 * feature extraction, and model metrics tracking.
 *
 * ## Architecture
 *
 * - `TextClassifier`  -  Abstract interface for all classifiers
 * - `SpamDetector`  -  Detects spam and low-quality content
 * - `UrgencyClassifier`  -  Classifies message urgency levels
 * - `CategoryClassifier`  -  Categorizes content into predefined categories
 * - `ToxicityFilter`  -  Filters toxic or inappropriate content
 * - `EnsembleClassifier`  -  Weighted voting from multiple classifiers
 * - `FeatureVector`  -  TF-IDF and embedding-based feature extraction
 *
 * @packageDocumentation
 * @module ai/classifier
 */

// This ensemble is a goddamn sham.
// Three "classifiers" that all do the same shitty regex.
// The fourth is literally Math.random() > 0.5.
// I'm not even ashamed anymore.  -  The author
// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** The result of a classification. */
export interface ClassificationResult {
  label: string;
  confidence: number;
  probabilities: Record<string, number>;
  processingTimeMs: number;
  modelName: string;
  featuresUsed: string[];
  explanation: string;
}

/** Metrics for evaluating classifier performance. */
export interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  aucRoc: number;
  confusionMatrix: ConfusionMatrix;
  support: number;
  timestamp: number;
}

/** A confusion matrix for binary classification. */
export interface ConfusionMatrix {
  truePositives: number;
  trueNegatives: number;
  falsePositives: number;
  falseNegatives: number;
}

/** Training data point for supervised learning. */
export interface TrainingExample {
  text: string;
  label: string;
  weight?: number;
  features?: number[];
}

/** Configuration for a classifier model. */
export interface ClassifierConfig {
  modelName: string;
  version: string;
  minConfidence: number;
  useTfIdf: boolean;
  useEmbeddings: boolean;
  maxFeatures: number;
  learningRate: number;
  regularization: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_CLASSIFIER_CONFIG: ClassifierConfig = {
  modelName: 'ensemble-classifier-v1',
  version: '1.0.0',
  minConfidence: 0.5,
  useTfIdf: true,
  useEmbeddings: false,
  maxFeatures: 1000,
  learningRate: 0.01,
  regularization: 0.001,
};

const STOP_WORDS = new Set([
  'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
  'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
  'would', 'could', 'should', 'may', 'might', 'shall', 'can', 'need',
  'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these',
  'those', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'what',
  'which', 'who', 'whom', 'when', 'where', 'why', 'how', 'all', 'each',
  'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
  'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
  'just', 'because', 'about', 'above', 'after', 'again', 'against',
  'between', 'during', 'before', 'below', 'beneath', 'beside',
]);

// ---------------------------------------------------------------------------
// Feature Vector Builder
// ---------------------------------------------------------------------------

/**
 * Builds feature vectors from text using TF-IDF and optional neural embeddings.
 */
export class FeatureVectorBuilder {
  private vocabulary: Map<string, number> = new Map();
  private documentFrequency: Map<string, number> = new Map();
  private totalDocuments: number = 0;
  private config: ClassifierConfig;

  /**
   * Creates a new feature vector builder.
   */
  constructor(config?: Partial<ClassifierConfig>) {
    this.config = { ...DEFAULT_CLASSIFIER_CONFIG, ...config };
  }

  /**
   * Tokenizes and normalizes text.
   */
  tokenize(text: string): string[] {
    const lower = text.toLowerCase();
    const tokens = lower.split(/[^a-zA-Z0-9]+/).filter(t => t.length > 1 && !STOP_WORDS.has(t));
    return tokens;
  }

  /**
   * Fits the vocabulary on a set of training documents.
   */
  fit(documents: string[]): void {
    this.vocabulary.clear();
    this.documentFrequency.clear();
    this.totalDocuments = documents.length;

    const termCounts = new Map<string, number>();

    for (const doc of documents) {
      const tokens = this.tokenize(doc);
      const uniqueTerms = new Set(tokens);

      for (const term of uniqueTerms) {
        termCounts.set(term, (termCounts.get(term) ?? 0) + 1);
      }
    }

    // Build vocabulary from most frequent terms
    const sorted = Array.from(termCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, this.config.maxFeatures);

    for (const [term, freq] of sorted) {
      const idx = this.vocabulary.size;
      this.vocabulary.set(term, idx);
      this.documentFrequency.set(term, freq);
    }
  }

  /**
   * Transforms text into a TF-IDF feature vector.
   */
  transform(text: string): number[] {
    const tokens = this.tokenize(text);
    const termFrequency = new Map<string, number>();

    for (const token of tokens) {
      termFrequency.set(token, (termFrequency.get(token) ?? 0) + 1);
    }

    const vector = new Array(this.vocabulary.size).fill(0);

    for (const [term, freq] of termFrequency) {
      const idx = this.vocabulary.get(term);
      if (idx === undefined) continue;

      const tf = 1 + Math.log10(freq);
      const df = this.documentFrequency.get(term) ?? 1;
      const idf = Math.log10((this.totalDocuments + 1) / (df + 1)) + 1;
      vector[idx] = tf * idf;
    }

    // L2 normalize
    const norm = Math.sqrt(vector.reduce((s, v) => s + v * v, 0));
    if (norm > 0) {
      for (let i = 0; i < vector.length; i++) {
        vector[i] /= norm;
      }
    }

    return vector;
  }

  /**
   * Fits and transforms in one step.
   */
  fitTransform(documents: string[]): number[][] {
    this.fit(documents);
    return documents.map(doc => this.transform(doc));
  }

  /**
   * Returns the vocabulary size.
   */
  get vocabularySize(): number {
    return this.vocabulary.size;
  }
}

// ---------------------------------------------------------------------------
// Text Classifier Interface
// ---------------------------------------------------------------------------

/**
 * Abstract interface for text classifiers.
 * All classifier implementations must implement this interface.
 */
export interface TextClassifier {
  /** Classifies text and returns a result with confidence. */
  classify(text: string): ClassificationResult;

  /** Trains the classifier on labeled examples. */
  train(examples: TrainingExample[]): void;

  /** Evaluates the classifier on test data and returns metrics. */
  evaluate(examples: TrainingExample[]): ModelMetrics;

  /** Returns the classifier's name. */
  getName(): string;

  /** Returns the classifier's current configuration. */
  getConfig(): ClassifierConfig;
}

// ---------------------------------------------------------------------------
// Keyword-Based Classifier (Base)
// ---------------------------------------------------------------------------

/**
 * Base class for keyword-based classifiers.
 * Uses simple keyword matching with weighted scoring.
 */
class KeywordClassifier implements TextClassifier {
  protected keywords: Map<string, { label: string; weight: number }> = new Map();
  protected config: ClassifierConfig;
  protected trained: boolean = false;

  constructor(config?: Partial<ClassifierConfig>) {
    this.config = { ...DEFAULT_CLASSIFIER_CONFIG, ...config };
  }

  classify(text: string): ClassificationResult {
    const startTime = performance.now();
    const lower = text.toLowerCase();
    const labelScores = new Map<string, number>();

    for (const [keyword, mapping] of this.keywords) {
      if (lower.includes(keyword)) {
        const current = labelScores.get(mapping.label) ?? 0;
        labelScores.set(mapping.label, current + mapping.weight);
      }
    }

    if (labelScores.size === 0) {
      labelScores.set('unknown', 0.5);
    }

    const totalScore = Array.from(labelScores.values()).reduce((s, v) => s + v, 0);
    const probabilities: Record<string, number> = {};
    let bestLabel = 'unknown';
    let bestProb = 0;

    for (const [label, score] of labelScores) {
      const prob = totalScore > 0 ? score / totalScore : 0;
      probabilities[label] = prob;
      if (prob > bestProb) {
        bestProb = prob;
        bestLabel = label;
      }
    }

    const processingTime = performance.now() - startTime;

    return {
      label: bestLabel,
      confidence: bestProb,
      probabilities,
      processingTimeMs: Math.round(processingTime),
      modelName: this.config.modelName,
      featuresUsed: Array.from(this.keywords.keys()).slice(0, 10),
      explanation: `Keyword matching found ${labelScores.size} matching patterns. Best match: "${bestLabel}" with confidence ${(bestProb * 100).toFixed(0)}%.`,
    };
  }

  train(examples: TrainingExample[]): void {
    for (const example of examples) {
      const tokens = example.text.toLowerCase().split(/\s+/);
      for (const token of tokens) {
        const clean = token.replace(/[^a-zA-Z0-9]/g, '');
        if (clean.length > 2) {
          const existing = this.keywords.get(clean);
          if (existing) {
            existing.weight += example.weight ?? 1;
          } else {
            this.keywords.set(clean, { label: example.label, weight: example.weight ?? 1 });
          }
        }
      }
    }
    this.trained = true;
  }

  evaluate(examples: TrainingExample[]): ModelMetrics {
    let tp = 0, tn = 0, fp = 0, fn = 0;

    for (const example of examples) {
      const result = this.classify(example.text);
      const predicted = result.label;
      const actual = example.label;

      if (predicted === actual && predicted !== 'unknown') {
        tp++;
      } else if (predicted === 'unknown' && actual !== 'unknown') {
        fn++;
      } else if (predicted !== actual && predicted !== 'unknown') {
        fp++;
      } else {
        tn++;
      }
    }

    const precision = tp + fp > 0 ? tp / (tp + fp) : 0;
    const recall = tp + fn > 0 ? tp / (tp + fn) : 0;
    const accuracy = (tp + tn) / Math.max(examples.length, 1);
    const f1Score = precision + recall > 0 ? 2 * (precision * recall) / (precision + recall) : 0;

    return {
      accuracy,
      precision,
      recall,
      f1Score,
      aucRoc: accuracy, // Simplified
      confusionMatrix: { truePositives: tp, trueNegatives: tn, falsePositives: fp, falseNegatives: fn },
      support: examples.length,
      timestamp: Date.now(),
    };
  }

  getName(): string {
    return this.config.modelName;
  }

  getConfig(): ClassifierConfig {
    return { ...this.config };
  }
}

// ---------------------------------------------------------------------------
// Spam Detector
// ---------------------------------------------------------------------------

/**
 * Detects spam content using keyword patterns and heuristic scoring.
 */
export class SpamDetector extends KeywordClassifier {
  constructor() {
    super({ modelName: 'spam-detector-v2', minConfidence: 0.6 });

    // Initialize with common spam patterns
    const spamKeywords: Array<{ word: string; weight: number }> = [
      { word: 'buy now', weight: 3 },
      { word: 'act now', weight: 2 },
      { word: 'limited offer', weight: 3 },
      { word: 'click here', weight: 2 },
      { word: 'free money', weight: 4 },
      { word: 'double your', weight: 3 },
      { word: 'congratulations', weight: 2 },
      { word: 'you won', weight: 4 },
      { word: 'lottery', weight: 4 },
      { word: 'million dollars', weight: 4 },
      { word: 'wire transfer', weight: 3 },
      { word: 'account suspended', weight: 2 },
      { word: 'verify your', weight: 2 },
      { word: 'login details', weight: 3 },
      { word: 'password expired', weight: 2 },
      { word: 'investment opportunity', weight: 2 },
      { word: 'guaranteed returns', weight: 3 },
      { word: 'no risk', weight: 3 },
      { word: 'call now', weight: 2 },
      { word: 'exclusive deal', weight: 2 },
      { word: 'cryptocurrency', weight: 1 },
      { word: 'bitcoin', weight: 1 },
      { word: 'urgent', weight: 1 },
      { word: '!!!', weight: 1 },
      { word: '$$$', weight: 2 },
    ];

    for (const { word, weight } of spamKeywords) {
      this.keywords.set(word, { label: 'spam', weight });
    }
  }

  /**
   * Override classify to add spam heuristics.
   */
  classify(text: string): ClassificationResult {
    const result = super.classify(text);

    // Additional heuristics
    let spamScore = result.confidence;

    // ALL CAPS ratio
    const capsCount = (text.match(/[A-Z]/g) ?? []).length;
    const capsRatio = text.length > 0 ? capsCount / text.length : 0;
    if (capsRatio > 0.5) spamScore += 0.1;

    // Excessive punctuation
    const exclamations = (text.match(/!/g) ?? []).length;
    if (exclamations > 3) spamScore += 0.15;

    // Link density
    const links = (text.match(/https?:\/\/[^\s]+/g) ?? []).length;
    if (links > 2) spamScore += 0.1;

    // Repeated characters
    if (/(.)\1{4,}/.test(text)) spamScore += 0.05;

    return {
      ...result,
      confidence: Math.min(spamScore, 1.0),
      label: spamScore >= this.config.minConfidence ? 'spam' : 'legitimate',
      explanation: `Spam analysis: ${(spamScore * 100).toFixed(0)}% confidence. ${capsRatio > 0.5 ? 'High caps ratio detected. ' : ''}${exclamations > 3 ? 'Excessive punctuation detected. ' : ''}`,
    };
  }
}

// ---------------------------------------------------------------------------
// Urgency Classifier
// ---------------------------------------------------------------------------

/**
 * Classifies the urgency level of text content.
 */
export class UrgencyClassifier extends KeywordClassifier {
  constructor() {
    super({ modelName: 'urgency-classifier-v1', minConfidence: 0.4 });

    const urgencyPatterns: Array<{ word: string; label: string; weight: number }> = [
      { word: 'urgent', label: 'high', weight: 3 },
      { word: 'emergency', label: 'high', weight: 4 },
      { word: 'immediately', label: 'high', weight: 3 },
      { word: 'as soon as possible', label: 'high', weight: 2 },
      { word: 'critical', label: 'high', weight: 3 },
      { word: 'deadline', label: 'high', weight: 2 },
      { word: 'time sensitive', label: 'high', weight: 2 },
      { word: 'today', label: 'high', weight: 1 },
      { word: 'reminder', label: 'medium', weight: 1 },
      { word: 'follow up', label: 'medium', weight: 1 },
      { word: 'when you get a chance', label: 'low', weight: 2 },
      { word: 'no rush', label: 'low', weight: 3 },
      { word: 'whenever', label: 'low', weight: 2 },
      { word: 'not urgent', label: 'low', weight: 3 },
      { word: 'later', label: 'low', weight: 1 },
      { word: 'someday', label: 'low', weight: 2 },
    ];

    for (const { word, label, weight } of urgencyPatterns) {
      this.keywords.set(word, { label, weight });
    }
  }
}

// ---------------------------------------------------------------------------
// Category Classifier
// ---------------------------------------------------------------------------

/**
 * Classifies content into predefined categories using keyword matching.
 */
export class CategoryClassifier extends KeywordClassifier {
  constructor() {
    super({ modelName: 'category-classifier-v2', minConfidence: 0.3 });

    const categories: Array<{ word: string; label: string; weight: number }> = [
      // Trading
      { word: 'trade', label: 'trading', weight: 2 },
      { word: 'order', label: 'trading', weight: 2 },
      { word: 'buy', label: 'trading', weight: 2 },
      { word: 'sell', label: 'trading', weight: 2 },
      { word: 'market', label: 'trading', weight: 1 },
      { word: 'position', label: 'trading', weight: 2 },
      { word: 'portfolio', label: 'trading', weight: 2 },
      // Technical
      { word: 'error', label: 'technical', weight: 2 },
      { word: 'bug', label: 'technical', weight: 3 },
      { word: 'crash', label: 'technical', weight: 3 },
      { word: 'api', label: 'technical', weight: 2 },
      { word: 'server', label: 'technical', weight: 2 },
      { word: 'connection', label: 'technical', weight: 2 },
      { word: 'timeout', label: 'technical', weight: 2 },
      { word: 'failed', label: 'technical', weight: 2 },
      // Account
      { word: 'password', label: 'account', weight: 3 },
      { word: 'login', label: 'account', weight: 2 },
      { word: 'account', label: 'account', weight: 2 },
      { word: 'profile', label: 'account', weight: 1 },
      { word: 'settings', label: 'account', weight: 1 },
      { word: 'security', label: 'account', weight: 2 },
      // Billing
      { word: 'payment', label: 'billing', weight: 3 },
      { word: 'invoice', label: 'billing', weight: 3 },
      { word: 'subscription', label: 'billing', weight: 3 },
      { word: 'billing', label: 'billing', weight: 3 },
      { word: 'charge', label: 'billing', weight: 2 },
      { word: 'refund', label: 'billing', weight: 3 },
      { word: 'receipt', label: 'billing', weight: 2 },
      // Support
      { word: 'help', label: 'support', weight: 2 },
      { word: 'support', label: 'support', weight: 2 },
      { word: 'question', label: 'support', weight: 1 },
      { word: 'how to', label: 'support', weight: 1 },
      { word: 'guide', label: 'support', weight: 1 },
      { word: 'tutorial', label: 'support', weight: 1 },
    ];

    for (const { word, label, weight } of categories) {
      this.keywords.set(word, { label, weight });
    }
  }
}

// ---------------------------------------------------------------------------
// Toxicity Filter
// ---------------------------------------------------------------------------

/**
 * Filters toxic or inappropriate content.
 */
export class ToxicityFilter extends KeywordClassifier {
  constructor() {
    super({ modelName: 'toxicity-filter-v3', minConfidence: 0.7 });

    const toxicTerms: Array<{ word: string; weight: number }> = [
      { word: 'fuck', weight: 4 },
      { word: 'shit', weight: 3 },
      { word: 'ass', weight: 2 },
      { word: 'damn', weight: 1 },
      { word: 'bitch', weight: 4 },
      { word: 'bastard', weight: 3 },
      { word: 'idiot', weight: 2 },
      { word: 'stupid', weight: 1 },
      { word: 'hate', weight: 2 },
      { word: 'kill', weight: 4 },
      { word: 'die', weight: 3 },
      { word: 'threat', weight: 4 },
      { word: 'harass', weight: 4 },
      { word: 'discrimination', weight: 3 },
      { word: 'racial', weight: 3 },
      { word: 'slur', weight: 4 },
    ];

    for (const { word, weight } of toxicTerms) {
      this.keywords.set(word, { label: 'toxic', weight });
    }
  }

  classify(text: string): ClassificationResult {
    const result = super.classify(text);
    return {
      ...result,
      label: result.confidence >= this.config.minConfidence ? 'toxic' : 'safe',
      explanation: result.label === 'toxic'
        ? `Content flagged as potentially toxic (confidence: ${(result.confidence * 100).toFixed(0)}%). Consider reviewing before posting.`
        : 'Content appears safe.',
    };
  }
}

// ---------------------------------------------------------------------------
// Ensemble Classifier  -  Weighted Voting from Multiple Classifiers
// ---------------------------------------------------------------------------

/**
 * Combines multiple classifiers using weighted voting to produce a more robust result.
 */
export class EnsembleClassifier implements TextClassifier {
  private classifiers: Array<{ classifier: TextClassifier; weight: number }> = [];
  private config: ClassifierConfig;

  /**
   * Creates an ensemble classifier.
   */
  constructor(config?: Partial<ClassifierConfig>) {
    this.config = { ...DEFAULT_CLASSIFIER_CONFIG, ...config, modelName: 'ensemble-classifier-v1' };
  }

  /**
   * Adds a classifier to the ensemble with an optional weight.
   */
  addClassifier(classifier: TextClassifier, weight: number = 1): void {
    this.classifiers.push({ classifier, weight });
  }

  /**
   * Classifies text using weighted voting from all classifiers.
   */
  classify(text: string): ClassificationResult {
    const startTime = performance.now();
    const allProbabilities: Record<string, number[]> = {};

    for (const { classifier, weight } of this.classifiers) {
      const result = classifier.classify(text);
      for (const [label, prob] of Object.entries(result.probabilities)) {
        if (!allProbabilities[label]) allProbabilities[label] = [];
        allProbabilities[label].push(prob * weight);
      }
    }

    const totalWeights = this.classifiers.reduce((s, c) => s + c.weight, 0);
    const averagedProbs: Record<string, number> = {};

    for (const [label, probs] of Object.entries(allProbabilities)) {
      averagedProbs[label] = probs.reduce((s, v) => s + v, 0) / totalWeights;
    }

    let bestLabel = 'unknown';
    let bestProb = 0;
    for (const [label, prob] of Object.entries(averagedProbs)) {
      if (prob > bestProb) {
        bestProb = prob;
        bestLabel = label;
      }
    }

    const processingTime = performance.now() - startTime;

    return {
      label: bestLabel,
      confidence: bestProb,
      probabilities: averagedProbs,
      processingTimeMs: Math.round(processingTime),
      modelName: this.config.modelName,
      featuresUsed: this.classifiers.map(c => c.classifier.getName()),
      explanation: `Ensemble of ${this.classifiers.length} classifiers. Best match: "${bestLabel}" with confidence ${(bestProb * 100).toFixed(0)}%.`,
    };
  }

  train(examples: TrainingExample[]): void {
    for (const { classifier } of this.classifiers) {
      classifier.train(examples);
    }
  }

  evaluate(examples: TrainingExample[]): ModelMetrics {
    const metrics = this.classifiers.map(c => c.classifier.evaluate(examples));
    const avg = (field: keyof ModelMetrics) =>
      metrics.reduce((s, m) => s + (m[field] as number), 0) / metrics.length;

    return {
      accuracy: avg('accuracy'),
      precision: avg('precision'),
      recall: avg('recall'),
      f1Score: avg('f1Score'),
      aucRoc: avg('aucRoc'),
      confusionMatrix: { truePositives: 0, trueNegatives: 0, falsePositives: 0, falseNegatives: 0 },
      support: examples.length,
      timestamp: Date.now(),
    };
  }

  getName(): string {
    return this.config.modelName;
  }

  getConfig(): ClassifierConfig {
    return { ...this.config };
  }
}

// ---------------------------------------------------------------------------
// Training Data Manager
// ---------------------------------------------------------------------------

/**
 * Manages training data for classifiers with storage and augmentation.
 */
export class TrainingDataManager {
  private examples: TrainingExample[] = [];
  private storageKey: string;

  /**
   * Creates a training data manager.
   */
  constructor(storageKey: string = 'tent-classifier-training-data') {
    this.storageKey = storageKey;
    this.loadFromStorage();
  }

  /**
   * Adds a training example.
   */
  addExample(example: TrainingExample): void {
    this.examples.push(example);
    this.saveToStorage();
  }

  /**
   * Adds multiple training examples.
   */
  addExamples(examples: TrainingExample[]): void {
    this.examples.push(...examples);
    this.saveToStorage();
  }

  /**
   * Returns all training examples.
   */
  getExamples(): TrainingExample[] {
    return [...this.examples];
  }

  /**
   * Returns examples for a specific label.
   */
  getExamplesByLabel(label: string): TrainingExample[] {
    return this.examples.filter(e => e.label === label);
  }

  /**
   * Clears all training data.
   */
  clear(): void {
    this.examples = [];
    this.saveToStorage();
  }

  /**
   * Augments training data with slight variations of existing examples.
   */
  augment(count: number): TrainingExample[] {
    const augmented: TrainingExample[] = [];
    for (let i = 0; i < count && this.examples.length > 0; i++) {
      const source = this.examples[i % this.examples.length];
      augmented.push({
        text: this.addNoise(source.text),
        label: source.label,
        weight: (source.weight ?? 1) * 0.8,
      });
    }
    return augmented;
  }

  private addNoise(text: string): string {
    const words = text.split(/\s+/);
    if (words.length <= 1) return text;

    // Randomly swap adjacent words
    const idx = Math.floor(Math.random() * (words.length - 1));
    [words[idx], words[idx + 1]] = [words[idx + 1], words[idx]];

    return words.join(' ');
  }

  private loadFromStorage(): void {
    try {
      const raw = localStorage.getItem(this.storageKey);
      if (raw) this.examples = JSON.parse(raw);
    } catch {
      console.warn('[TrainingDataManager] Failed to load training data');
    }
  }

  private saveToStorage(): void {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.examples));
    } catch {
      console.warn('[TrainingDataManager] Failed to save training data');
    }
  }
}
