import matplotlib.pyplot as plt
import io
import os

def create_chart(df, title, xlabel, ylabel, id_col, value_col, color='blue', filename='exercise_chart.png'):
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.bar(df[id_col].astype(str), df[value_col], color=color)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticklabels(df[id_col].astype(str), rotation=45)
    fig.tight_layout()

    chart_path = os.path.join('static', 'images', filename)
    
    print(f"Saving chart to: {chart_path}")

    os.makedirs(os.path.dirname(chart_path), exist_ok=True)
    
    try:
        fig.savefig(chart_path)
        print(f"Chart successfully saved as: {chart_path}")
    except Exception as e:
        print(f"Error saving chart: {e}")
    
    plt.close()
    
    print(f"Returning filename: {filename}")  # Debugging statement
    return filename
