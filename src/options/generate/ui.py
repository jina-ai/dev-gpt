import random
from dataclasses import dataclass

product_manager_names = [
    ('Leon', 'm'),
    ('Saahil', 'm',),
    ('Susana', 'f')
]
engineer_names = [
    ('Aaron', 'm'),
    ('Alaeddine', 'm'),
    ('Andrei', 'm'),
    ('Anne', 'f'),
    ('Bo', 'm'),
    ('Charlotte', 'f'),
    ('David', 'm'),
    ('Deepankar', 'm'),
    ('Delgermurun', 'm'),
    ('Edward', 'm'),
    ('Felix', 'm'),
    ('Florian', 'm'),
    ('Georgios', 'm'),
    ('Girish', 'm'),
    ('Guillaume', 'm'),
    ('Isabelle', 'f'),
    ('Jackmin', 'm'),
    ('Jie', 'm'),
    ('Joan', 'm'),
    ('Johannes', 'm'),
    ('Joschka', 'm'),
    ('Lechun', 'm'),
    ('Louis', 'm'),
    ('Mark', 'm'),
    ('Maximilian', 'm'),
    ('Michael', 'm'),
    ('Mohamed Aziz', 'm'),
    ('Mohammad Kalim', 'm'),
    ('Nikos', 'm'),
    ('Ran', 'm'),
    ('Saba', 'f'),
    ('Sami', 'm'),
    ('Sha', 'm'),
    ('Subba Reddy', 'm'),
    ('Tanguy', 'm'),
    ('Winston', 'm'),
    ('Yadh', 'm'),
    ('Yanlong', 'm'),
    ('Zac', 'm'),
    ('Zhaofeng', 'm'),
    ('Zihao', 'm'),
    ('Ziniu', 'm')
]

role_to_gender_to_emoji = {
    'engineer':{
        'm': '👨‍💻',
        'f': '👩‍💻'
    },
    'pm': {
        'm': '👨‍💼',
        'f': '👩‍💼'
    },
    'qa_endineer': {
        'm': '👨‍🔧',
        'f': '👩‍🔧',
    },
}

@dataclass
class Employee:
    role: str
    name: str
    gender: str
    emoji: str

def get_random_employee(role: str) -> Employee:
    name, gender = random.choice(product_manager_names)
    emoji = role_to_gender_to_emoji[role][gender]
    return Employee(role, name, gender, emoji)
