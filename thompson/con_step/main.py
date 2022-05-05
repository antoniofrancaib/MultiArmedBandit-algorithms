from cmath import isnan
import random
from xml.sax import parseString
import numpy as np
import matplotlib.pyplot as plt
import copy


#import time

from mab import *

class Campaign():

    def __init__(self,id,budget,spent,impressions,conversions,roi):
        #falta determinar como podemos saber el tiempo que lleva la campaña 
        self.id = id    
        self.budget = budget #daily budget
        self.spent = spent
        self.impressions = impressions
        self.conversions = conversions
        self.roi = roi

    def update(self,impressions,conversions,roi):
        self.spent += self.budget
        self.impressions += int(impressions)
        self.conversions += int(conversions)
        self.roi = float(roi)

    def change_budget(self,increment):
        #increment debe ser un valor numerico para editar el ( daily budget )
        self.budget = self.budget + increment
    

class State(Campaign):

    def __init__(self,budget,total_time,campaigns,initial_allocation=0):
        self.budget = budget
        self.time = total_time
        self.campaigns = campaigns
        self.current_time = 0
        self.current_budget = self.budget/self.time
        #dictionary that contains all states, where the key is a timestamp
        self.history = {}
        self.budget_allocation = {}
        self.remaining = budget

        self.step = 0.005

        self.k_arms = len(campaigns)

        self.stopped = []
        if initial_allocation == 0: 
            self.initial_allocation()
        else:
            for campaign in campaigns:
                self.budget_allocation[campaign.id] = initial_allocation[campaign.id]

    def next_step(self):
        self.current_time += 1
        print(f'time {self.current_time}')
        self.remaining-=self.current_budget
        if self.remaining <= 0:
            raise Exception('No budget left')
        #increase the capacity of an agent to take significant budget decisions
        self.step *= 1.001


    def get_reward(self):
        if self.current_time == 0:
            return list(np.zeros(len(self.budget_allocation)))
        rewards = [] 
        for campaign in self.campaigns:
            rewards.append(campaign.roi*self.current_budget*self.budget_allocation[campaign.id])
        norm = [float(i)/sum(rewards) for i in rewards]
        print(f'The rewards at timestamp {self.current_time} is {rewards}')
        return norm

    def take_action(self,arm,dec):
        if self.current_time < 1:
            pass
        else: 
            print(f'AI is increasing budget of campaign {arm}')
            self.act3(arm,dec)
        b = copy.deepcopy(self.budget_allocation)
        rewards = self.get_reward()
        self.history[self.current_time] = [b,rewards]
        print(f'Current state: {self.budget_allocation} at timestamp {self.current_time}')
        self.allocate_budget()
        self.next_step()
        return rewards

    def act3(self,arm,dec):
        temp_budget = copy.deepcopy(self.budget_allocation)
        temp_budget[arm] += self.step
        if dec not in self.stopped:
            temp_budget[dec] -= self.step
            if temp_budget[dec] < 0: 
                temp_budget[dec] = 0
                self.stopped.append(dec)
        else:
            a = True
            while a:
                dec = random.randint(0,len(self.campaigns)-1)
                if dec != arm:
                    if dec not in self.stopped:
                        temp_budget[dec] -= self.step
                        print(f'Ai has decreased campaign {dec}')
                    a = False
           
        for campaign in temp_budget:
            temp_budget[campaign] = round(temp_budget[campaign],8)
        #validate that the budget is corrent before updating it
        if self.validate_budget(temp_budget):
            self.budget_allocation = temp_budget
        else:
            print(f"Chosen arm: {arm}, Stopped Campaigns: {self.stopped}")
            raise Exception(f'Budget is not valid, act3 policy has failed, Failed budget is {temp_budget}')
            
    def act2(self,arm,q_values):
        population = list(range(len(self.campaigns)))
        step = self.step
        temp_budget = copy.deepcopy(self.budget_allocation)
        temp_budget[arm] += step
        q_values = q_values.tolist()
        # SOLUTION TO BUG ID 7
        #print(f"---{len(population)-len(self.stopped)}")
        #time.sleep(0.01)
        if len(population)-len(self.stopped)==1:
            temp_budget[arm] = 1
        else:
            #if we have no data, randomly decrease an campaign
            if all(v == 0 for v in q_values):
                dec = random.randint(0,len(self.campaigns)-1)
                if dec != arm:
                    temp_budget[dec] -= step
                else:
                    while dec == arm:
                        dec = random.randint(0,len(self.campaigns)-1)
                    temp_budget[dec] -= step
            #if we have data, take a stochastic approach 
            else:
                norm = [float(i)/sum(q_values) for i in q_values]
                decrease_prob = [1-p for p in norm]
                #print(f'norm is {norm}')
                #print(f'population is {population}')
                dec = int(random.choices(population, weights=decrease_prob, k=1)[0])
                #we could test another action policy where the chosen arm would be also subject to a decrease, 
                # that would result in no action, I'll ignore that option 
                if dec != arm and dec not in self.stopped:
                    #TODO SOLUTION OF BUG 1
                    if temp_budget[dec] < step:
                        temp_budget[arm] -= temp_budget[dec]
                        #temp_budget[arm] -= step
                        temp_budget[dec] = 0
                        print(f'##### Campaign {dec} was stopped completely ###')
                        #TODO delete campaign from the state ( make it ignore it )
                        self.stopped.append(dec)
                    else:
                        temp_budget[dec] -= step
                else:
                    while True:
                        dec = int(random.choices(population, weights=decrease_prob, k=1)[0])
                        if dec == arm:
                            continue
                        if dec in self.stopped:
                            continue
                        else:
                            break
                    #SOLUTION OF BUG 1
                    if temp_budget[dec] < step:
                        temp_budget[arm] -= temp_budget[dec]
                        temp_budget[arm] -= step
                        temp_budget[dec] = 0
                        print(f'##### Campaign {dec} was stopped completely ###')
                        self.stopped.append(dec)
                    else:
                        temp_budget[dec] -= step
                print(f'Ai has decreased campaign {dec} given probs {decrease_prob}')
        #round the budget to avoid RuntimeWarning: invalid value encountered in double_scalars
        for campaign in temp_budget:
            temp_budget[campaign] = round(temp_budget[campaign],8)
        #validate that the budget is corrent before updating it
        if self.validate_budget(temp_budget):
            #update budget
            self.budget_allocation = temp_budget
        else:
            print(f"Chosen arm: {arm}, Stopped Campaigns: {self.stopped}")
            raise Exception(f'Budget is not valid, act2 policy has failed, Failed budget is {temp_budget}')
            
    @staticmethod        
    def get_state(budget_allocation):
        return tuple(budget_allocation.values())

    def initial_allocation(self):
        for campaign in self.campaigns:
            self.budget_allocation[campaign.id] = round(1/len(self.campaigns),8)
        b = copy.deepcopy(self.budget_allocation)
        self.history[self.current_time] = [b,self.get_reward()]
        self.allocate_budget()

    def allocate_budget(self):
        #turns a distribution into a value
        #campaign budget = current budget * campaign%allocation
        for campaign in self.campaigns:
            campaign.budget = round(self.current_budget*self.budget_allocation[campaign.id],8)
        
    @staticmethod
    def validate_budget(budget_allocation):
        total = 0
        for campaign in budget_allocation.values():
            if campaign > 1: return False
            elif campaign < 0: return False
            else:
                total += campaign
        total = round(total,4)
        if total > 0.95 and total <= 1.025:
            return True
        else: return False
    
    def dynamic(self):
        for campaign in self.campaigns:
            a = random.randint(0,2)
            if a == 0:
                campaign.roi *= 1.05
            elif a == 1:
                if campaign.roi > 1:
                    campaign.roi *= 0.95
                elif campaign.roi > 0:
                    campaign.roi *= 0.99
                else:
                    campaign.roi *= 1.01
            else: 
                return self
    
                