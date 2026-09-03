import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import minimize

def solve_beta_parameters(mean, mode, a, b):
    """Solve for alpha and beta parameters of a generalized beta distribution
    given the mean, mode, and range [a, b]."""
    # Handle edge case where mode is at the boundary
    if mode == a:
        # Special case: If mode is at lower bound, alpha < 1
        alpha = mean * 0.5  # Starting guess for alpha < 1
        beta = alpha * (b - mean) / (mean - a)
        return alpha, beta
    elif mode == b:
        # Special case: If mode is at upper bound, beta < 1
        beta = 0.5  # Starting guess for beta < 1
        alpha = beta * (mean - a) / (b - mean)
        return alpha, beta
    
    # Normalized mean and mode (in [0,1] range)
    norm_mean = (mean - a) / (b - a)
    norm_mode = (mode - a) / (b - a)
    
    def objective(params):
        alpha, beta = params
        # Calculate theoretical mean and mode
        theo_mean = alpha / (alpha + beta)
        theo_mode = (alpha - 1) / (alpha + beta - 2) if alpha > 1 and beta > 1 else 0.5
        # Return squared error
        return (theo_mean - norm_mean)**2 + (theo_mode - norm_mode)**2
    
    # Initial guess
    x0 = [2.0, 2.0]
    bounds = [(0.1, None), (0.1, None)]
    
    # Optimize
    result = minimize(objective, x0, bounds=bounds)
    alpha, beta = result.x
    
    return alpha, beta

def plot_generalized_beta(alpha, beta, a, b, output_file='beta_distribution.png', data_points=None):
    """Plot the generalized beta distribution with given parameters."""
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
    
    # Generate x values and calculate PDF
    x = np.linspace(a, b, 200)
    x_scaled = (x - a) / (b - a)
    pdf = stats.beta.pdf(x_scaled, alpha, beta) / (b - a)
    
    # Plot PDF
    ax1.plot(x, pdf, 'b-', lw=2, label=f'Beta(α={alpha:.2f}, β={beta:.2f})')
    
    # Plot data points if provided
    if data_points is not None:
        ax1.scatter(data_points, np.zeros_like(data_points), color='red', 
                   alpha=0.5, label='Data Points', zorder=5)
    
    # Calculate statistics
    mean = a + (b - a) * alpha / (alpha + beta)
    var = (b - a)**2 * (alpha * beta) / ((alpha + beta)**2 * (alpha + beta + 1))
    
    if alpha > 1 and beta > 1:
        mode = a + (b - a) * (alpha - 1) / (alpha + beta - 2)
        ax1.axvline(mode, color='red', linestyle='--', alpha=0.7,
                   label=f'Mode = {mode:.2f}')
    
    # Add mean line
    ax1.axvline(mean, color='green', linestyle='--', alpha=0.7,
                label=f'Mean = {mean:.2f}')
    
    # Add statistics text
    stats_text = f"α = {alpha:.2f}, β = {beta:.2f}\n"
    stats_text += f"Mean = {mean:.3f}\n"
    stats_text += f"Variance = {var:.3f}\n"
    stats_text += f"Range: [{a:.2f}, {b:.2f}]"
    
    if data_points is not None:
        stats_text += f"\nData points: {len(data_points)}"
    
    ax1.text(1.02, 0.5, stats_text, transform=ax1.transAxes,
             bbox=dict(facecolor='white', alpha=0.8))
    
    # Configure first plot
    ax1.set_title('Generalized Beta Distribution PDF')
    ax1.set_xlabel('x')
    ax1.set_ylabel('Probability Density')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Generate and plot sample data
    sample_data = a + (b - a) * np.random.beta(alpha, beta, 1000)
    ax2.hist(sample_data, bins=30, density=True, alpha=0.6,
             color='gray', label='Sample Data')
    ax2.plot(x, pdf, 'r-', lw=2, label='True Distribution')
    ax2.set_title(f'Sample Histogram (n=1000)')
    ax2.set_xlabel('x')
    ax2.set_ylabel('Density')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def plot_lognormal(mu, sigma, output_file='lognormal_distribution.png', data_points=None, reverse=False):
    """Plot the log-normal or reverse log-normal distribution with given parameters."""
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
    
    # Generate x values and calculate PDF
    x = np.linspace(0, np.exp(mu + 4*sigma), 200)
    if reverse:
        # For reverse log-normal, we use the same x values but flip the PDF
        pdf = stats.lognorm.pdf(x, sigma, loc=0, scale=np.exp(mu))
        pdf = pdf[::-1]  # Reverse the PDF array
        x = x[::-1]      # Reverse the x array to match
    else:
        pdf = stats.lognorm.pdf(x, sigma, loc=0, scale=np.exp(mu))
    
    # Plot PDF
    dist_type = "Reverse LogNormal" if reverse else "LogNormal"
    ax1.plot(x, pdf, 'b-', lw=2, label=f'{dist_type}(μ={mu:.2f}, σ={sigma:.2f})')
    
    # Plot data points if provided
    if data_points is not None:
        ax1.scatter(data_points, np.zeros_like(data_points), color='red', 
                   alpha=0.5, label='Data Points', zorder=5)
    
    # Calculate statistics
    mean = np.exp(mu + sigma**2/2)
    var = (np.exp(sigma**2) - 1) * np.exp(2*mu + sigma**2)
    mode = np.exp(mu - sigma**2)
    
    # Add mean and mode lines
    ax1.axvline(mean, color='green', linestyle='--', alpha=0.7,
                label=f'Mean = {mean:.2f}')
    ax1.axvline(mode, color='red', linestyle='--', alpha=0.7,
                label=f'Mode = {mode:.2f}')
    
    # Add statistics text
    stats_text = f"μ = {mu:.2f}, σ = {sigma:.2f}\n"
    stats_text += f"Mean = {mean:.3f}\n"
    stats_text += f"Variance = {var:.3f}\n"
    stats_text += f"Mode = {mode:.3f}"
    
    if data_points is not None:
        stats_text += f"\nData points: {len(data_points)}"
    
    ax1.text(1.02, 0.5, stats_text, transform=ax1.transAxes,
             bbox=dict(facecolor='white', alpha=0.8))
    
    # Configure first plot
    ax1.set_title(f'{dist_type} Distribution PDF')
    ax1.set_xlabel('x')
    ax1.set_ylabel('Probability Density')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Generate and plot sample data
    sample_data = np.random.lognormal(mu, sigma, 1000)
    if reverse:
        # For reverse log-normal, we need to transform the samples
        max_val = np.exp(mu + 4*sigma)
        sample_data = max_val - sample_data
    ax2.hist(sample_data, bins=30, density=True, alpha=0.6,
             color='gray', label='Sample Data')
    ax2.plot(x, pdf, 'r-', lw=2, label='True Distribution')
    ax2.set_title(f'Sample Histogram (n=1000)')
    ax2.set_xlabel('x')
    ax2.set_ylabel('Density')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def get_data_points():
    """Get a list of numbers from user input."""
    print("\nEnter numbers (one per line). Press Enter twice when done:")
    numbers = []
    while True:
        try:
            line = input()
            if line == "":
                break
            numbers.append(float(line))
        except ValueError:
            print("Error: Please enter valid numbers")
            continue
    return np.array(numbers)

def main():
    print("Distribution Fitter")
    print("------------------")
    
    # Choose distribution type
    while True:
        dist_type = input("Choose distribution type:\n1. Beta distribution\n2. Log-normal distribution\n3. Reverse log-normal distribution\nChoice (1/2/3): ")
        if dist_type in ['1', '2', '3']:
            break
        print("Error: Please enter 1, 2, or 3")
    
    # Choose input method
    while True:
        choice = input("Choose input method:\n1. Enter parameters directly\n2. Enter a list of numbers\nChoice (1/2): ")
        if choice in ['1', '2']:
            break
        print("Error: Please enter 1 or 2")
    
    if dist_type == '1':  # Beta distribution
        # Get data based on choice
        if choice == '1':
            while True:
                try:
                    mean = float(input("Enter the desired mean: "))
                    break
                except ValueError:
                    print("Error: Please enter a valid number")
            data_points = None
        else:
            data_points = get_data_points()
            if len(data_points) == 0:
                print("Error: No numbers were entered")
                return
            mean = np.mean(data_points)
            print(f"\nCalculated mean: {mean:.3f}")
        
        # Get remaining parameters
        while True:
            try:
                mode = float(input("Enter the desired mode: "))
                a = float(input("Enter the lower bound (a): "))
                b = float(input("Enter the upper bound (b): "))
                
                # Validate input
                if a >= b:
                    print("Error: Lower bound must be less than upper bound")
                    continue
                if mean < a or mean > b:
                    print("Error: Mean must be between lower and upper bounds")
                    continue
                if mode < a or mode > b:
                    print("Error: Mode must be between lower and upper bounds")
                    continue
                if data_points is not None and (np.any(data_points < a) or np.any(data_points > b)):
                    print("Error: All data points must be within the specified bounds")
                    continue
                break
            except ValueError:
                print("Error: Please enter valid numbers")
        
        # Solve for parameters
        try:
            alpha, beta = solve_beta_parameters(mean, mode, a, b)
            print(f"\nFitted parameters:")
            print(f"α = {alpha:.2f}")
            print(f"β = {beta:.2f}")
            
            # Generate filename with parameters
            filename = f"beta_dist_mean{mean:.2f}_mode{mode:.2f}_range{a:.2f}-{b:.2f}.png"
            output_file = f'/mnt/g/SOCIAL_PAPER/beta_distribution/{filename}'
            
            # Generate and save plot
            plot_generalized_beta(alpha, beta, a, b, output_file, data_points)
            print(f"\nPlot saved as: {output_file}")
            
        except Exception as e:
            print(f"Error: Could not fit beta distribution with these parameters: {str(e)}")
            print("Try different values for mean, mode, or range.")
    
    else:  # Log-normal or reverse log-normal distribution
        reverse = dist_type == '3'
        if choice == '1':
            while True:
                try:
                    mean = float(input("Enter the desired mean: "))
                    std = float(input("Enter the desired standard deviation: "))
                    if std <= 0:
                        print("Error: Standard deviation must be positive")
                        continue
                    if mean <= 0:
                        print("Error: Mean must be positive")
                        continue
                    break
                except ValueError:
                    print("Error: Please enter valid numbers")
            
            # Convert to log-normal parameters
            mu = np.log(mean**2 / np.sqrt(mean**2 + std**2))
            sigma = np.sqrt(np.log(1 + std**2 / mean**2))
            data_points = None
        else:
            data_points = get_data_points()
            if len(data_points) == 0:
                print("Error: No numbers were entered")
                return
            if np.any(data_points <= 0):
                print("Error: All data points must be positive")
                return
            
            # Calculate log-normal parameters from data
            log_data = np.log(data_points)
            mu = np.mean(log_data)
            sigma = np.std(log_data)
            mean = np.exp(mu + sigma**2/2)
            std = np.sqrt((np.exp(sigma**2) - 1) * np.exp(2*mu + sigma**2))
            print(f"\nCalculated mean: {mean:.3f}")
            print(f"Calculated standard deviation: {std:.3f}")
        
        # Generate filename with parameters
        dist_name = "reverse_lognormal" if reverse else "lognormal"
        filename = f"{dist_name}_dist_mean{mean:.2f}_std{std:.2f}.png"
        output_file = f'/mnt/g/SOCIAL_PAPER/beta_distribution/{filename}'
        
        # Generate and save plot
        plot_lognormal(mu, sigma, output_file, data_points, reverse)
        print(f"\nPlot saved as: {output_file}")

if __name__ == "__main__":
    main() 