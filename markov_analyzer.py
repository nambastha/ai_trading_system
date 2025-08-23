import numpy as np
import pandas as pd
from sklearn.preprocessing import KBinsDiscretizer
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class MarkovChainAnalyzer:
    def __init__(self, n_states: int = 5):
        self.n_states = n_states
        self.transition_matrix = None
        self.state_labels = None
        self.discretizer = None
        self.current_state = None
        
    def _discretize_returns(self, returns: pd.Series) -> np.ndarray:
        """Convert continuous returns into discrete states"""
        # Remove NaN values
        clean_returns = returns.dropna().values.reshape(-1, 1)
        
        if len(clean_returns) == 0:
            return np.array([])
        
        # Use quantile-based discretization for better state distribution
        self.discretizer = KBinsDiscretizer(
            n_bins=self.n_states, 
            encode='ordinal', 
            strategy='quantile'
        )
        
        states = self.discretizer.fit_transform(clean_returns).flatten().astype(int)
        
        # Create meaningful state labels
        boundaries = self.discretizer.bin_edges_[0]
        self.state_labels = {
            0: f"Strong Sell (<{boundaries[1]:.3f})",
            1: f"Sell ({boundaries[1]:.3f} to {boundaries[2]:.3f})",
            2: f"Hold ({boundaries[2]:.3f} to {boundaries[3]:.3f})",
            3: f"Buy ({boundaries[3]:.3f} to {boundaries[4]:.3f})",
            4: f"Strong Buy (>{boundaries[4]:.3f})"
        }
        
        return states
    
    def build_transition_matrix(self, price_data: pd.DataFrame) -> np.ndarray:
        """Build Markov chain transition matrix from price data"""
        try:
            # Calculate daily returns
            returns = price_data['Close'].pct_change()
            
            # Discretize returns into states
            states = self._discretize_returns(returns)
            
            if len(states) < 2:
                logger.error("Insufficient data to build transition matrix")
                return np.zeros((self.n_states, self.n_states))
            
            # Initialize transition matrix
            self.transition_matrix = np.zeros((self.n_states, self.n_states))
            
            # Count transitions
            for i in range(len(states) - 1):
                current_state = states[i]
                next_state = states[i + 1]
                self.transition_matrix[current_state, next_state] += 1
            
            # Normalize to get probabilities
            row_sums = self.transition_matrix.sum(axis=1)
            # Avoid division by zero
            for i in range(self.n_states):
                if row_sums[i] > 0:
                    self.transition_matrix[i, :] /= row_sums[i]
                else:
                    # If no transitions from this state, assume uniform distribution
                    self.transition_matrix[i, :] = 1.0 / self.n_states
            
            # Set current state based on most recent return
            if len(states) > 0:
                self.current_state = states[-1]
            
            logger.info(f"Built transition matrix with {len(states)} observations")
            return self.transition_matrix
            
        except Exception as e:
            logger.error(f"Error building transition matrix: {str(e)}")
            return np.zeros((self.n_states, self.n_states))
    
    def predict_next_states(self, n_steps: int = 1) -> Dict[int, float]:
        """Predict probability distribution of states after n steps"""
        if self.transition_matrix is None or self.current_state is None:
            return {}
        
        # Start with current state
        current_prob = np.zeros(self.n_states)
        current_prob[self.current_state] = 1.0
        
        # Apply transition matrix n times
        for _ in range(n_steps):
            current_prob = current_prob @ self.transition_matrix
        
        return {state: prob for state, prob in enumerate(current_prob)}
    
    def get_trading_signal(self, confidence_threshold: float = 0.6) -> Dict:
        """Generate trading signal based on Markov chain predictions"""
        if self.transition_matrix is None:
            return {'signal': 'HOLD', 'confidence': 0.0, 'reason': 'No model available'}
        
        # Predict next state probabilities
        next_state_probs = self.predict_next_states(1)
        
        # Calculate buy/sell probabilities
        buy_prob = next_state_probs.get(3, 0) + next_state_probs.get(4, 0)  # Buy + Strong Buy
        sell_prob = next_state_probs.get(0, 0) + next_state_probs.get(1, 0)  # Strong Sell + Sell
        hold_prob = next_state_probs.get(2, 0)  # Hold
        
        # Determine signal
        max_prob = max(buy_prob, sell_prob, hold_prob)
        
        if max_prob < confidence_threshold:
            signal = 'HOLD'
            confidence = max_prob
            reason = f'Low confidence ({max_prob:.2f} < {confidence_threshold})'
        elif buy_prob == max_prob:
            signal = 'BUY'
            confidence = buy_prob
            reason = f'Markov chain predicts upward movement (prob: {buy_prob:.2f})'
        elif sell_prob == max_prob:
            signal = 'SELL'
            confidence = sell_prob
            reason = f'Markov chain predicts downward movement (prob: {sell_prob:.2f})'
        else:
            signal = 'HOLD'
            confidence = hold_prob
            reason = f'Markov chain suggests sideways movement (prob: {hold_prob:.2f})'
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reason': reason,
            'state_probabilities': next_state_probs,
            'current_state': self.current_state,
            'current_state_label': self.state_labels.get(self.current_state, 'Unknown') if self.state_labels else 'Unknown'
        }
    
    def get_long_term_outlook(self, days: int = 5) -> Dict:
        """Get longer-term outlook using multi-step predictions"""
        if self.transition_matrix is None:
            return {}
        
        outlook = {}
        for day in range(1, days + 1):
            day_probs = self.predict_next_states(day)
            buy_prob = day_probs.get(3, 0) + day_probs.get(4, 0)
            sell_prob = day_probs.get(0, 0) + day_probs.get(1, 0)
            
            if buy_prob > sell_prob:
                outlook[f'day_{day}'] = {'trend': 'BULLISH', 'confidence': buy_prob}
            elif sell_prob > buy_prob:
                outlook[f'day_{day}'] = {'trend': 'BEARISH', 'confidence': sell_prob}
            else:
                outlook[f'day_{day}'] = {'trend': 'NEUTRAL', 'confidence': max(buy_prob, sell_prob)}
        
        return outlook
    
    def analyze_pattern_strength(self) -> Dict:
        """Analyze the strength and reliability of detected patterns"""
        if self.transition_matrix is None:
            return {}
        
        # Calculate entropy to measure predictability
        entropy = 0
        for i in range(self.n_states):
            for j in range(self.n_states):
                if self.transition_matrix[i, j] > 0:
                    entropy -= self.transition_matrix[i, j] * np.log2(self.transition_matrix[i, j])
        
        max_entropy = np.log2(self.n_states)
        predictability = 1 - (entropy / (self.n_states * max_entropy))
        
        # Find most likely transitions
        strong_transitions = []
        for i in range(self.n_states):
            max_prob_idx = np.argmax(self.transition_matrix[i, :])
            max_prob = self.transition_matrix[i, max_prob_idx]
            if max_prob > 0.4:  # Strong transition threshold
                strong_transitions.append({
                    'from_state': i,
                    'to_state': max_prob_idx,
                    'probability': max_prob,
                    'from_label': self.state_labels.get(i, f'State {i}'),
                    'to_label': self.state_labels.get(max_prob_idx, f'State {max_prob_idx}')
                })
        
        return {
            'predictability_score': predictability,
            'entropy': entropy,
            'strong_transitions': strong_transitions,
            'transition_matrix': self.transition_matrix.tolist()
        }
