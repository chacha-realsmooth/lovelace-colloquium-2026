import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def stats(df):
    #remove all webpages that were unable to be loaded due to external factors
    rot_df = df.drop(df[df.status_code == 0].index)
    total_count = len(rot_df)

    #account for all status codes
    se_error_pages = rot_df[rot_df['status_code'].astype(str).str.contains('5')]
    se_error_count = len(se_error_pages)

    cl_error_pages = rot_df[rot_df['status_code'].astype(str).str.contains('4')]
    cl_error_count = len(cl_error_pages)

    redirect_pages = rot_df[rot_df['status_code'].astype(str).str.contains('3')]
    redirect_count = len(redirect_pages)

    success_pages = rot_df[rot_df['status_code'].astype(str).str.contains('2')]
    success_count = len(success_pages)

    rot_percent = round(((se_error_count + cl_error_count + redirect_count) / total_count * 100), 2)
    success_percent = round((success_count / total_count * 100), 2)

    print(f"total pages: {total_count}\nsuccessful pages (2xx): {success_count}\nserver-side error pages(5xx): {se_error_count}\nclient-side error pages (4xx): {cl_error_count}\nredirected pages (3xx): {redirect_count}\npercent of pages rotted: {rot_percent}%\npercent of pages successfully loaded: {success_percent}%")

    return (total_count, se_error_count, cl_error_count, redirect_count,success_count, rot_percent, success_percent)

def pie_plot(stats):
    counts = [stats[1],stats[2],stats[3],stats[4]]
    labels = ["Server-side Error","Client-side Error","Redirection","Success"]
    # explode success part of pie chart for easier viewing
    myexplode = [0, 0, 0, 0.2]
    plt.pie(counts,labels=labels,explode=myexplode, autopct='%1.1f%%')
    plt.legend(title = "Status Codes:")
    plt.title("HTTP Status Results for Bangor University")
    
    plt.show()

def duo_plot(rot_percents,total_pages):
    fig, ax1 = plt.subplots()

    # create barplot
    sns.barplot(x=["Lovelace","Bangor","Bath"], y=rot_percents, ax=ax1, color='navy')
    ax1.set_ylabel('Rot Percent', fontsize=12, color='navy')
    ax1.set_xlabel('Website', color = 'black')

    # create secondary y-axis
    ax2 = ax1.twinx()

    # create lineplot
    sns.lineplot(x=["Lovelace","Bangor","Bath"], y=total_pages, ax=ax2, color='darkred', marker='o')
    ax2.set_ylabel('Total Pages on Website', fontsize=12, color='darkred')

    ax1.yaxis.label.set_color('navy')
    ax2.yaxis.label.set_color('darkred')
    ax1.tick_params(axis='y', colors='navy')
    ax2.tick_params(axis='y', colors='darkred')

    plt.show()


def main():
    lovelace_df = pd.read_csv("lovelace_urls.csv")
    bangor_df = pd.read_csv("bangor_urls.csv")
    bath_df = pd.read_csv("bath_urls.csv")

    lovelace_stats = stats(lovelace_df)
    bangor_stats = stats(bangor_df)
    bath_stats = stats(bath_df)

    rot_percents = []
    total_pages = []

    rot_percents.append(lovelace_stats[5])
    rot_percents.append(bangor_stats[5])
    rot_percents.append(bath_stats[5])
    total_pages.append(lovelace_stats[0])
    total_pages.append(bangor_stats[0])
    total_pages.append(bath_stats[0])

    # change parameter for each dataset
    pie_plot(bangor_stats)
    # duo_plot(rot_percents,total_pages)


main()