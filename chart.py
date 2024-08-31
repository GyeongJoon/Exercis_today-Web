import matplotlib.pyplot as plt
import os
from matplotlib import font_manager, rc

def create_chart(df, title, xlabel, ylabel, x_column, y_column, color='blue', filename='chart.png'):
    
    font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    rc('font', family=font_manager.FontProperties(fname=font_path).get_name())
    
    plt.figure(figsize=(8, 5))
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
