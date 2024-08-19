import matplotlib.pyplot as plt
import io
import os

def create_chart(df, title, xlabel, ylabel, x_column, y_column, color='blue', filename='chart.png'):
    plt.figure(figsize=(10, 6))
    plt.bar(df[x_column], df[y_column], color=color)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # 저장 경로 지정
    save_path = os.path.join('static', 'images', filename)
    plt.savefig(save_path)
    plt.close()
    
    return filename
