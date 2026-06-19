/**
 * TradePage - Main trading interface for the Tent of Trials platform.
 *
 * This page composes the trading UI components: order book, chart,
 * trade form, position list, and order history. It manages the data
 * flow between these components and handles real-time updates from
 * the WebSocket market data feed.
 *
 * The page layout adapts to screen size:
 *   - Desktop (>1200px): Full layout with chart, order book, trade form
 *   - Tablet (768-1200px): Stacked layout with tabs
 *   - Mobile (<768px): Single column with collapsible sections
 *
 * TODO: The responsive layout uses CSS media queries AND JavaScript
 * resize listeners. This dual approach causes a brief flash of wrong
 * layout on initial render because the CSS and JS disagree about the
 * breakpoint. The JS-based layout detection uses 1200px while the CSS
 * uses 1199px. This 1px difference was introduced when the design
 * team updated the breakpoints but only updated the CSS variables.
 *
 * TODO: The trade form validation logic is duplicated between this
 * component and the API service layer. The client-side validation
 * catches common errors (insufficient funds, invalid order size)
 * but the server-side validation is the authoritative check. When
 * the two disagree, the user sees a confusing "order rejected" error
 * after the UI said the order was valid. The two validation systems
 * should use the same rules, but they're implemented in different
 * languages (TypeScript and Rust) and are not synchronized.
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { OrderBook } from '../components/OrderBook';
import { TradingChart } from '../components/TradingChart';
import { useMarketData } from '../hooks/useMarketData';
import { useWebSocket } from '../hooks/useWebSocket';
import { getDataService } from '../utils/dataService';

// ---------------------------------------------------------------------------
// TYPES
// ---------------------------------------------------------------------------

type TabKey = 'chart' | 'orderbook' | 'trades' | 'positions' | 'orders' | 'info';

interface TabConfig {
  key: TabKey;
  label: string;
  icon?: string;
}

// ---------------------------------------------------------------------------
// CONSTANTS
// ---------------------------------------------------------------------------

const TABS: TabConfig[] = [
  { key: 'chart', label: 'Chart', icon: '📈' },
  { key: 'orderbook', label: 'Order Book', icon: '📊' },
  { key: 'trades', label: 'Trades', icon: '🔄' },
  { key: 'positions', label: 'Positions', icon: '💼' },
  { key: 'orders', label: 'Orders', icon: '📋' },
  { key: 'info', label: 'Info', icon: 'ℹ️' },
];

const TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'] as const;

const ORDER_TYPES = ['market', 'limit', 'stop', 'stop_limit'] as const;

const SIDES = ['buy', 'sell'] as const;

// ---------------------------------------------------------------------------
// COMPONENT
// ---------------------------------------------------------------------------

export function TradePage() {
  const [activeTab, setActiveTab] = useState<TabKey>('chart');
  const [selectedInstrument, setSelectedInstrument] = useState('BTC/USD');
  const [timeframe, setTimeframe] = useState<typeof TIMEFRAMES[number]>('1h');
  const [orderSide, setOrderSide] = useState<'buy' | 'sell'>('buy');
  const [orderType, setOrderType] = useState<typeof ORDER_TYPES[number]>('limit');
  const [orderPrice, setOrderPrice] = useState('');
  const [orderQuantity, setOrderQuantity] = useState('');
  const [orderTotal, setOrderTotal] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chartType, setChartType] = useState<'candlestick' | 'line' | 'area'>('candlestick');
  const [showIndicators, setShowIndicators] = useState(false);
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>([]);
  const [layout, setLayout] = useState<'default' | 'compact' | 'fullscreen'>('default');

  const marketData = useMarketData({
    instrumentIds: [selectedInstrument],
    throttleMs: 100,
    maxTrades: 50,
  });

  const ws = useWebSocket({
    url: `wss://api.example.com/ws?instrument=${selectedInstrument}`,
    autoConnect: true,
    reconnect: true,
  });

  const dataService = useMemo(() => getDataService(), []);

  // Fetch initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        const instruments = await dataService.fetchInstruments();
        const orderBook = await dataService.fetchOrderBook(selectedInstrument);
        const candles = await dataService.fetchCandles(selectedInstrument, timeframe);
        const trades = await dataService.fetchRecentTrades(selectedInstrument);
      } catch (err) {
        console.error('Failed to load market data:', err);
      }
    };
    loadData();
  }, [selectedInstrument, timeframe, dataService]);

  // Calculate order total
  useEffect(() => {
    const price = parseFloat(orderPrice);
    const quantity = parseFloat(orderQuantity);
    if (!isNaN(price) && !isNaN(quantity)) {
      setOrderTotal((price * quantity).toFixed(2));
    } else {
      setOrderTotal('');
    }
  }, [orderPrice, orderQuantity]);

  const handlePriceClick = useCallback((price: number, side: 'buy' | 'sell') => {
    setOrderPrice(price.toString());
    setOrderSide(side);
    setActiveTab('orders');
  }, []);

  const handleSubmitOrder = useCallback(async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const order = {
        instrument: selectedInstrument,
        side: orderSide,
        type: orderType,
        price: orderType !== 'market' ? parseFloat(orderPrice) : undefined,
        quantity: parseFloat(orderQuantity),
        timeInForce: 'gtc',
      };

      const result = await dataService.placeOrder(order);
      // TODO: Show success notification
      setOrderPrice('');
      setOrderQuantity('');
      setOrderTotal('');
    } catch (err: any) {
      setError(err?.message || 'Failed to place order');
    } finally {
      setIsSubmitting(false);
    }
  }, [selectedInstrument, orderSide, orderType, orderPrice, orderQuantity, dataService]);

  const handleInstrumentChange = useCallback((instrument: string) => {
    setSelectedInstrument(instrument);
    setOrderPrice('');
    setOrderQuantity('');
    setOrderTotal('');
    setError(null);
  }, []);

  const handleTimeframeChange = useCallback((tf: typeof TIMEFRAMES[number]) => {
    setTimeframe(tf);
  }, []);

  const handleToggleIndicator = useCallback((indicator: string) => {
    setSelectedIndicators(prev =>
      prev.includes(indicator)
        ? prev.filter(i => i !== indicator)
        : [...prev, indicator]
    );
  }, []);

  // Calculate price from total
  const handleTotalChange = useCallback((total: string) => {
    setOrderTotal(total);
    const qty = parseFloat(orderQuantity);
    const tot = parseFloat(total);
    if (!isNaN(qty) && !isNaN(tot) && qty > 0) {
      setOrderPrice((tot / qty).toFixed(2));
    }
  }, [orderQuantity]);

  // Calculate quantity from total
  const handleQuantityFromTotal = useCallback(() => {
    const price = parseFloat(orderPrice);
    const total = parseFloat(orderTotal);
    if (!isNaN(price) && !isNaN(total) && price > 0) {
      setOrderQuantity((total / price).toFixed(6));
    }
  }, [orderPrice, orderTotal]);

  // Quick percentage buttons for order quantity
  const handleQuickQuantity = useCallback((pct: number) => {
    // TODO: Calculate based on available balance
    const mockBalance = 10000;
    const price = orderType !== 'market' ? parseFloat(orderPrice) || 1 : 1;
    const quantity = (mockBalance * pct / 100) / price;
    setOrderQuantity(quantity.toFixed(6));
  }, [orderPrice, orderType]);

  // The tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'chart':
        return (
          <TradingChart
            data={[]}
            symbol={selectedInstrument}
            timeframe={timeframe}
            height={500}
            showTimeframes={true}
            config={{
              layout: { background: '#0f172a' },
            }}
          />
        );
      case 'orderbook':
        return (
          <div style={{ border: '1px solid #334155', borderRadius: 12, overflow: 'hidden' }}>
            <OrderBook
              data={null}
              instrumentSymbol={selectedInstrument.split('/')[0]}
              quoteCurrency={selectedInstrument.split('/')[1] || 'USD'}
              onPriceClick={handlePriceClick}
              maxRows={15}
              compact={false}
            />
          </div>
        );
      case 'trades':
        return (
          <div style={{ padding: 16, border: '1px solid #334155', borderRadius: 12 }}>
            <h3 style={{ marginBottom: 16, color: '#f8fafc' }}>Recent Trades</h3>
            {marketData.recentTrades.length === 0 ? (
              <div style={{ color: '#64748b', textAlign: 'center', padding: 40 }}>
                No recent trades for {selectedInstrument}
              </div>
            ) : (
              <table style={{ width: '100%', fontSize: 13 }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'right' }}>Price</th>
                    <th style={{ textAlign: 'right' }}>Size</th>
                    <th style={{ textAlign: 'right' }}>Total</th>
                    <th style={{ textAlign: 'right' }}>Time</th>
                    <th style={{ textAlign: 'center' }}>Side</th>
                  </tr>
                </thead>
                <tbody>
                  {marketData.recentTrades.map(trade => (
                    <tr key={trade.id}>
                      <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                        {trade.price.toFixed(2)}
                      </td>
                      <td style={{ textAlign: 'right' }}>{trade.volume.toFixed(4)}</td>
                      <td style={{ textAlign: 'right' }}>{(trade.price * trade.volume).toFixed(2)}</td>
                      <td style={{ textAlign: 'right', color: '#64748b', fontSize: 11 }}>
                        {new Date(trade.timestamp).toLocaleTimeString()}
                      </td>
                      <td style={{
                        textAlign: 'center',
                        color: trade.side === 'buy' ? '#22c55e' : '#ef4444',
                        fontWeight: 600,
                      }}>
                        {trade.side.toUpperCase()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        );
      case 'positions':
        return (
          <div style={{ padding: 16, border: '1px solid #334155', borderRadius: 12 }}>
            <h3 style={{ marginBottom: 16, color: '#f8fafc' }}>Open Positions</h3>
            <div style={{ color: '#64748b', textAlign: 'center', padding: 40 }}>
              No open positions
            </div>
          </div>
        );
      case 'orders':
        return (
          <div style={{ padding: 16, border: '1px solid #334155', borderRadius: 12 }}>
            <h3 style={{ marginBottom: 16, color: '#f8fafc' }}>Place Order</h3>

            {/* Side toggle */}
            <div style={{ display: 'flex', gap: 0, marginBottom: 16 }}>
              <button
                onClick={() => setOrderSide('buy')}
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  border: 'none',
                  borderRadius: '8px 0 0 8px',
                  background: orderSide === 'buy' ? '#22c55e' : '#1e293b',
                  color: orderSide === 'buy' ? '#fff' : '#64748b',
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: 14,
                }}
              >
                Buy
              </button>
              <button
                onClick={() => setOrderSide('sell')}
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  border: 'none',
                  borderRadius: '0 8px 8px 0',
                  background: orderSide === 'sell' ? '#ef4444' : '#1e293b',
                  color: orderSide === 'sell' ? '#fff' : '#64748b',
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: 14,
                }}
              >
                Sell
              </button>
            </div>

            {/* Order type */}
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>
                Order Type
              </label>
              <div style={{ display: 'flex', gap: 4 }}>
                {ORDER_TYPES.map(type => (
                  <button
                    key={type}
                    onClick={() => setOrderType(type)}
                    style={{
                      flex: 1,
                      padding: '6px 8px',
                      fontSize: 11,
                      border: '1px solid',
                      borderRadius: 6,
                      borderColor: orderType === type ? '#3b82f6' : '#334155',
                      background: orderType === type ? 'rgba(59,130,246,0.15)' : 'transparent',
                      color: orderType === type ? '#60a5fa' : '#94a3b8',
                      cursor: 'pointer',
                      fontWeight: orderType === type ? 600 : 400,
                      textTransform: 'capitalize',
                    }}
                  >
                    {type.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            {/* Price field */}
            {orderType !== 'market' && (
              <div style={{ marginBottom: 12 }}>
                <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>
                  Price ({selectedInstrument.split('/')[1] || 'USD'})
                </label>
                <input
                  type="number"
                  value={orderPrice}
                  onChange={e => setOrderPrice(e.target.value)}
                  placeholder="0.00"
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: 8,
                    color: '#f8fafc',
                    fontSize: 14,
                    fontFamily: 'monospace',
                    outline: 'none',
                  }}
                />
              </div>
            )}

            {/* Quantity field */}
            <div style={{ marginBottom: 8 }}>
              <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>
                Quantity ({selectedInstrument.split('/')[0]})
              </label>
              <input
                type="number"
                value={orderQuantity}
                onChange={e => setOrderQuantity(e.target.value)}
                placeholder="0.000000"
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  background: '#0f172a',
                  border: '1px solid #334155',
                  borderRadius: 8,
                  color: '#f8fafc',
                  fontSize: 14,
                  fontFamily: 'monospace',
                  outline: 'none',
                }}
              />
            </div>

            {/* Quick quantity buttons */}
            <div style={{ display: 'flex', gap: 4, marginBottom: 12 }}>
              {[25, 50, 75, 100].map(pct => (
                <button
                  key={pct}
                  onClick={() => handleQuickQuantity(pct)}
                  style={{
                    flex: 1,
                    padding: '4px 8px',
                    fontSize: 11,
                    border: '1px solid #334155',
                    borderRadius: 4,
                    background: 'transparent',
                    color: '#64748b',
                    cursor: 'pointer',
                  }}
                >
                  {pct}%
                </button>
              ))}
            </div>

            {/* Total field */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>
                Total
              </label>
              <input
                type="number"
                value={orderTotal}
                onChange={e => handleTotalChange(e.target.value)}
                placeholder="0.00"
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  background: '#0f172a',
                  border: '1px solid #334155',
                  borderRadius: 8,
                  color: '#f8fafc',
                  fontSize: 14,
                  fontFamily: 'monospace',
                  outline: 'none',
                }}
              />
            </div>

            {/* Error message */}
            {error && (
              <div style={{
                padding: '8px 12px',
                marginBottom: 12,
                background: 'rgba(239,68,68,0.1)',
                border: '1px solid rgba(239,68,68,0.3)',
                borderRadius: 8,
                color: '#f87171',
                fontSize: 12,
              }}>
                {error}
              </div>
            )}

            {/* Submit button */}
            <button
              onClick={handleSubmitOrder}
              disabled={isSubmitting || !orderQuantity || (orderType !== 'market' && !orderPrice)}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: 'none',
                borderRadius: 8,
                background: orderSide === 'buy' ? '#22c55e' : '#ef4444',
                color: '#fff',
                fontWeight: 700,
                fontSize: 15,
                cursor: 'pointer',
                opacity: isSubmitting ? 0.7 : 1,
              }}
            >
              {isSubmitting
                ? 'Submitting...'
                : `${orderSide === 'buy' ? 'Buy' : 'Sell'} ${selectedInstrument}`
              }
            </button>
          </div>
        );
      case 'info':
        return (
          <div style={{ padding: 16, border: '1px solid #334155', borderRadius: 12 }}>
            <h3 style={{ marginBottom: 16, color: '#f8fafc' }}>Instrument Info</h3>
            <div style={{ color: '#94a3b8', fontSize: 13, lineHeight: 1.8 }}>
              <p>Symbol: <strong style={{ color: '#e2e8f0' }}>{selectedInstrument}</strong></p>
              <p>Exchange: <strong style={{ color: '#e2e8f0' }}>Internal</strong></p>
              <p>Status: <strong style={{ color: '#22c55e' }}>Trading</strong></p>
              <p>Type: <strong style={{ color: '#e2e8f0' }}>Crypto Spot</strong></p>
              <p>Min Order: <strong style={{ color: '#e2e8f0' }}>0.001</strong></p>
              <p>Max Order: <strong style={{ color: '#e2e8f0' }}>1000</strong></p>
              <p>Tick Size: <strong style={{ color: '#e2e8f0' }}>0.01</strong></p>
              <p>Lot Size: <strong style={{ color: '#e2e8f0' }}>0.000001</strong></p>
              <p>Leverage: <strong style={{ color: '#e2e8f0' }}>1x - 10x</strong></p>
              <p>Maker Fee: <strong style={{ color: '#e2e8f0' }}>0.10%</strong></p>
              <p>Taker Fee: <strong style={{ color: '#e2e8f0' }}>0.20%</strong></p>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{ padding: 16, maxWidth: 1400, margin: '0 auto' }}>
      {/* Header bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 16,
        flexWrap: 'wrap',
        gap: 12,
      }}>
        {/* Instrument selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <select
            value={selectedInstrument}
            onChange={e => handleInstrumentChange(e.target.value)}
            style={{
              padding: '8px 12px',
              background: '#1e293b',
              border: '1px solid #334155',
              borderRadius: 8,
              color: '#f8fafc',
              fontSize: 16,
              fontWeight: 600,
            }}
          >
            <option value="BTC/USD">BTC/USD</option>
            <option value="ETH/USD">ETH/USD</option>
            <option value="SOL/USD">SOL/USD</option>
            <option value="AVAX/USD">AVAX/USD</option>
            <option value="LINK/USD">LINK/USD</option>
            <option value="MATIC/USD">MATIC/USD</option>
            <option value="DOT/USD">DOT/USD</option>
            <option value="UNI/USD">UNI/USD</option>
          </select>

          {/* Connection indicator */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 12,
            color: marketData.connectionStatus === 'connected' ? '#22c55e' : '#ef4444',
          }}>
            <div style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: marketData.connectionStatus === 'connected' ? '#22c55e' : '#ef4444',
            }} />
            {marketData.connectionStatus}
          </div>
        </div>

        {/* Market ticker */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          fontFamily: 'monospace',
          fontSize: 14,
        }}>
          <span style={{ color: '#94a3b8' }}>Last:</span>
          <span style={{ color: '#f8fafc', fontWeight: 700, fontSize: 18 }}>
            {marketData.tick?.price?.toFixed(2) || '---'}
          </span>
          <span style={{ color: (marketData.tick?.change || 0) >= 0 ? '#22c55e' : '#ef4444' }}>
            {(marketData.tick?.change || 0) >= 0 ? '+' : ''}
            {marketData.tick?.change?.toFixed(2) || '---'}
            ({(marketData.tick?.changePercent || 0) >= 0 ? '+' : ''}
            {marketData.tick?.changePercent?.toFixed(2) || '---'}%)
          </span>
          <span style={{ color: '#64748b', fontSize: 12 }}>
            24h Vol: {marketData.tick?.volume24h?.toFixed(0) || '---'}
          </span>
        </div>
      </div>

      {/* Tab navigation */}
      <div style={{
        display: 'flex',
        gap: 0,
        marginBottom: 16,
        borderBottom: '1px solid #334155',
      }}>
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '10px 20px',
              border: 'none',
              borderBottom: activeTab === tab.key ? '2px solid #3b82f6' : '2px solid transparent',
              background: 'transparent',
              color: activeTab === tab.key ? '#f8fafc' : '#64748b',
              fontSize: 13,
              fontWeight: activeTab === tab.key ? 600 : 400,
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Content area */}
      <div>
        {renderTabContent()}
      </div>
    </div>
  );
}

export default TradePage;
