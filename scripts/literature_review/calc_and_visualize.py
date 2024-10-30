import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

def analyze_skewness():
    """
    Analyze skewness in similarity scores.
    
    Skewness measures the asymmetry of a distribution:
    - Positive skewness: longer/fatter tail on right (more extreme positive values)
    - Negative skewness: longer/fatter tail on left (more extreme negative values)
    - Zero skewness: symmetric distribution
    
    In our context:
    - Positive skewness: Author has occasional strong realist arguments
    - Negative skewness: Author has occasional strong moralist arguments
    - Near-zero skewness: Author is consistently balanced
    """
    
    # Create output directory
    Path("out").mkdir(exist_ok=True)
    Path("out/authors").mkdir(exist_ok=True)
    
    # Get all score files
    score_files = list(Path("scores").glob("*.csv"))
    
    results = []
    
    for file_path in score_files:
        # Read scores
        df = pd.read_csv(file_path)
        scores = df['score'].values
        
        # Get author name
        author = file_path.stem.split('__')[0][:100]
        
        # Calculate skewness and its statistical significance
        skewness = stats.skew(scores)
        skewtest_statistic, skewtest_pvalue = stats.skewtest(scores)
        
        # Calculate mean and standard deviation for context
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        # Calculate what percentage of scores are > 2 std from mean
                # Calculate what percentage of scores are > 2 std or < -2 std from mean
        upper_threshold = mean_score + (2 * std_score)
        lower_threshold = mean_score - (2 * std_score)
        pct_extreme_positive = np.mean(scores > upper_threshold) * 100
        pct_extreme_negative = np.mean(scores < lower_threshold) * 100
        pct_extreme_total = pct_extreme_positive + pct_extreme_negative
        
        results.append({
            'author': author,
            'skewness': skewness,
            'skewness_pvalue': skewtest_pvalue,
            'mean_score': mean_score,
            'std_score': std_score,
            'pct_extreme_positive': pct_extreme_positive,  # Realist extremes
            'pct_extreme_negative': pct_extreme_negative,  # Moralist extremes
            'pct_extreme_total': pct_extreme_total,
            'n_samples': len(scores)
        })

        # Create a larger figure with higher DPI
        plt.figure(figsize=(20, 8), dpi=300)        
        
        # Update visualization to show both thresholds         
        plt.subplot(1, 2, 1)
        sns.histplot(scores, kde=True)
        plt.axvline(x=mean_score, color='r', linestyle='--', label='Mean')
        plt.axvline(x=upper_threshold, color='g', linestyle='--', label='+2σ threshold')
        plt.axvline(x=lower_threshold, color='g', linestyle='--', label='-2σ threshold')
        plt.title(f'Score Distribution for {author}\nSkewness: {skewness:.2f}', fontsize=12)
        plt.xlabel('Score (Realist - Moralist)', fontsize=10)
        plt.ylabel('Count', fontsize=10)
        plt.legend(fontsize=8)
        
        # Add QQ plot to check for normality
        plt.subplot(1, 2, 2)
        stats.probplot(scores, dist="norm", plot=plt)
        plt.title("Q-Q Plot", fontsize=12)
        
        plt.tight_layout()
        plt.savefig(f'out/authors/{author}_skewness_analysis.png', 
                   bbox_inches='tight', 
                   dpi=300)
        plt.close()
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Sort by skewness from most negative (moralist) to most positive (realist)
    results_df = results_df.sort_values('skewness', ascending=True)
    
    # Save detailed results
    results_df.to_csv('out/skewness_analysis.csv', index=False)
    
    # Create visualization of skewness spectrum with larger size
    plt.figure(figsize=(30, 18))
    
    # Create more room for labels
    plt.subplots_adjust(left=0.3)  # Adjust left margin for labels
    
    # Plot authors by skewness
    y_pos = np.arange(len(results_df))
    colors = ['red' if p < 0.05 else 'gray' for p in results_df['skewness_pvalue']]
    
    plt.barh(y_pos, results_df['skewness'], align='center', alpha=0.8, color=colors)
    plt.yticks(y_pos, results_df['author'], fontsize=10)  # Adjust font size if needed
    plt.xlabel('Skewness (← Moralist Extremes | Realist Extremes →)', fontsize=12)
    plt.title('Author Skewness Analysis\nRed bars indicate statistically significant skewness (p < 0.05)', 
             fontsize=14, pad=20)
    
    # Add vertical line at 0
    plt.axvline(x=0, color='black', linestyle='--', alpha=0.5)
    
    # Add annotations for extreme percentages only (no sample size)
    for i, row in enumerate(results_df.itertuples()):
        plt.text(-max(abs(results_df['skewness'])), i, 
                f'M:{row.pct_extreme_negative:.1f}% | R:{row.pct_extreme_positive:.1f}%', 
                ha='right', va='center')
    
    plt.tight_layout()
    plt.savefig('out/skewness_spectrum.png', bbox_inches='tight', dpi=400)
    plt.close()
    
    # Print summary
    print("\nSkewness Analysis Summary:")
    print(f"Processed {len(results_df)} authors")
    print("\nAuthors with strongest Realist extremes (positive skew):")
    print(results_df[results_df['skewness'] > 0].head(3)[['author', 'skewness', 'skewness_pvalue', 'n_samples']])
    print("\nAuthors with strongest Moralist extremes (negative skew):")
    print(results_df[results_df['skewness'] < 0].head(3)[['author', 'skewness', 'skewness_pvalue', 'n_samples']])
    print("\nMost balanced authors (near-zero skew):")
    results_df['abs_skewness'] = abs(results_df['skewness'])
    print(results_df.nsmallest(3, 'abs_skewness')[['author', 'skewness', 'skewness_pvalue', 'n_samples']])

if __name__ == "__main__":
    analyze_skewness()