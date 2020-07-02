# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.ioff()
import matplotlib.dates as mdates
import numpy as np
from datetime import timedelta

def create_image(name,data,type):
    #Types: line_graph, pi_chart
    fig,ax = plt.subplots()
    fig.set_size_inches(5,5)
    if type == "line_graph": line_graph(ax,data)
    elif type == "pi_chart": pi_chart(ax,data)
    fig.savefig("tmp/{}.png".format(name))

def line_graph(ax,data):
    new_data = data.sort_values(by="date_made")
    fulldates = new_data["date_made"].tolist()
    fullvals = new_data["amount"].tolist()
    fulllabs = new_data["to"].tolist()
    categories = {}
    for i in range(len(fulldates)):
        if fulllabs[i] not in categories:
            categories[fulllabs[i]] = fullvals[i]
        else:
            categories[fulllabs[i]] += fullvals[i]
    valdata = categories.items()
    valdata = sorted(valdata,key=lambda x:x[1],reverse=True)
    categories = {}
    if len(valdata) > 6:
        for key,val in valdata[:5]:
            categories[key] = [[],[]]
        categories["other"] = [[],[]]
        valdata = valdata[:5] + [("other",0)]
    else:
        for key,val in valdata:
            categories[key] = [[],[]]
    for i in range(len(fulldates)):
        if fulllabs[i] in categories:
            categories[fulllabs[i]][0].append(fulldates[i])
            categories[fulllabs[i]][1].append(fullvals[i])
        else:
            categories["other"][0].append(fulldates[i])
            categories["other"][1].append(fullvals[i])
    try:
        currdatekey = fulldates[0]
        prevvals = {currdatekey:0}
        while currdatekey != fulldates[-1]:
            currdatekey = currdatekey + timedelta(days=1)
            prevvals[currdatekey] = 0
        valdata.reverse()
        for key,val in valdata:
            newvals = {skey:val for skey,val in prevvals.items()}
            skeys = sorted(newvals.keys())
            dates,amounts = categories[key]
            for i in range(len(dates)):
                newvals[dates[i]] += amounts[i]
            ax.bar(skeys,[newvals[skey] for skey in skeys],bottom=[prevvals[skey] for skey in skeys],label=key)
            #ax.fill_between(skeys,[prevvals[skey] for skey in skeys],[newvals[skey] for skey in skeys],label=key)
            prevvals = newvals
        ax.legend()
        for tick in ax.get_xticklabels():
            ticktext = tick.get_text()
            ticktext = ticktext.split("-")
            tick.set_text(ticktext[2]+"/"+ticktext[1]+"/"+ticktext[0])
            tick.set_rotation(45)
        fig.subplots_adjust(bottom=0.15)
    except:
        pass

def pi_chart(ax,data):
    new_data = data.sort_values(by=["amount"],ascending=False)
    ##Work out 'others' thing
    labels = new_data["to"].tolist()
    amounts = new_data["amount"].tolist()
    if len(amounts) > 6:
        newsum = sum(amounts[5:])
        amounts = amounts[:5] + [newsum]
        labels = labels[:5] + ["others"]
    ax.pie(amounts,labels=labels)

#Legacy code below here
def create_pi_chart(labels,amounts,output_name):
	fig,ax = plt.subplots()
	fig.set_size_inches(5,5)
	explode_amounts = 0.1*(1 - (np.argsort(amounts)/float(len(amounts))))
	ax.pie(amounts,labels=labels,autopct=lambda percent: str(0.01*int(np.round(percent*sum(amounts)))),explode=explode_amounts)
	fig.savefig("PdfTemp/"+output_name)

def create_bar_chart(categories,dates,breakdowns,output_name):
	fig,ax = plt.subplots()
	fig.set_size_inches(5,5)
	last_amounts = [0 for item in dates]
	for category,breakdown in zip(categories,breakdowns):
		ax.bar(dates,breakdown,bottom=last_amounts,label=category)
		last_amounts = [lam + nam for lam,nam in zip(last_amounts,breakdown)]
	date_dict = {7:"Sunday",0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",4:"Friday",5:"Saturday"}
	ax.set_xticks(dates)
	ax.set_xticklabels([date_dict[date_number] for date_number in dates])
	box = ax.get_position()
	ax.set_position([box.x0,box.y0,box.width*0.8,box.height])
	ax.legend(loc='center left',bbox_to_anchor=(1,0.5))
	fig.savefig("PdfTemp/"+output_name)

def create_filled_graph(categories,dates,breakdowns,output_name):
	sums = np.array([sum(item) for item in breakdowns])
	order_args = np.argsort(sums)
	categories = list(np.array(categories)[order_args][::-1])
	breakdowns = list(np.array(breakdowns)[order_args][::-1])
	fig,ax = plt.subplots()
	fig.set_size_inches(5,5)
	last_amounts = [0 for item in dates]
	for category,breakdown in zip(categories,breakdowns):
		new_amounts = [lam + nam for lam,nam in zip(last_amounts,breakdown)]
		ax.fill_between(dates,last_amounts,new_amounts,label=category)
		last_amounts = new_amounts
	box = ax.get_position()
	ax.set_position([box.x0,box.y0,box.width*0.8,box.height])
	ax.legend(loc='center left',bbox_to_anchor=(1,0.5))
	fig.savefig("PdfTemp/"+output_name)
