from cmath import isnan
from dataclasses import dataclass
import random
from xml.sax import parseString
import numpy as np
from thompson.con_step import *

@dataclass
class Campaign():
    def __init__(self, id, budget, impressions, conversions, roi):
        """Campaign Object with information about the campaign. We instantiate campaigns from this object."""
        self.id = id
        self.budget = budget  # daily budget
        self.impressions = [impressions]
        self.conversions = [conversions]

        self.roi = [roi]
        self.spent =[]


class State(Campaign):
    def __init__(self, total_budget, total_time, campaigns, t_campaigns, initial_percentual_allocation):
        """State Object with information about the state. We instantiate states from this object."""
        self.total_budget = total_budget
        self.remaining_budget = total_budget
        self.total_time = total_time
        self.campaigns = campaigns
        self.t_campaigns = t_campaigns
        self.spent = []
        self.current_time = 0
        self.current_budget = self.remaining_budget / self.total_time
        self.history = {}  # key is time step, value is state
        self.budget_percentual_allocation = initial_percentual_allocation
        self.step = 0.005
        self.max_step = 0.01

    def update(self, distribution):
        """updates the budget_distribution in the state"""
        for i, campaign in enumerate(self.budget_percentual_allocation):
            self.budget_percentual_allocation[campaign] = distribution[i]

        """updates budgets allocating the assigned budget to each campaign"""
        for campaign in self.campaigns:
            campaign.budget = round(self.current_budget * self.budget_percentual_allocation[campaign.id], 8)

        """updates current_time, increase step, and remaining_budget"""
        self.step = min(self.step * 1.001, self.max_step)
        self.current_time += 1
        self.remaining_budget -= self.spent[-1]


    def dynamic(self, budget_distribution):
        """gives new ROI, gives new spent, i.e. simulates an interaction with the real world"""
        for campaign in self.campaigns:
            campaign.roi.append(max(np.random.uniform(campaign.roi[-1] - 0.2, campaign.roi[-1] + 0.2), 0.5))

        total_spent = []
        for i, budget in enumerate(budget_distribution):
            percentual_spent = random.randint(95, 100)
            spent = (percentual_spent / 100)*budget
            total_spent.append(spent)
        self.spent.append(sum(total_spent))
        for i, campaign in enumerate(self.campaigns):
            campaign.spent.append(total_spent[i])
