# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

from mongoengine.document import Document, EmbeddedDocument
from mongoengine.fields import DictField, StringField, ListField, URLField, ReferenceField, IntField
from data_model.event import DataModelEvent
import requests


attack_url = 'https://attack.mitre.org'
proxies = {}

class AttackTactic(Document):
    name = StringField()
    url = URLField()
    description = StringField()
    order = IntField()


class AttackTechnique(Document):
    tactics = ListField(ReferenceField(AttackTactic))
    technique_id = StringField(unique=True)
    name = StringField()
    description = StringField()
    url = URLField()


class TechniqueMapping(EmbeddedDocument):
    LOW = 'Low'
    MODERATE = 'Moderate'
    HIGH = 'High'

    technique = ReferenceField(AttackTechnique)
    tactics = ListField(ReferenceField(AttackTactic))
    # Likely will ignore this field
    level = StringField(choices=[LOW, MODERATE, HIGH])


# tactics should be a SET, but we are not strictly enforcing that for now
class TacticSet(Document):
    tactics = ListField(ReferenceField(AttackTactic))

    def intersect(self, other, new=False):
        if isinstance(other, TacticSet):
            tactics = other.tactics
        else:
            tactics = other

        result = {tactic for tactic in self.tactics if tactic in tactics}

        if new:
            return TacticSet(tactics=result)
        else:
            return result

    def is_subset(self, other):
        if isinstance(other, TacticSet):
            tactics = other.tactics
        else:
            tactics = other

        return all(tactic in self.tactics for tactic in tactics)


def refresh_attack():
    params = dict(action='ask', format='json')
    params['query'] = """
        [[Category:Tactic]]
        |?Has description
    """
    tactic_results = requests.get("{}/{}".format(attack_url, 'api.php'), proxies=proxies, params=params, verify=False).json()
    tactics = {}
    for page, result in tactic_results['query']['results'].items():
        name = result['fulltext']
        tactic = AttackTactic.objects(name=name).first()

        if tactic is None:
            tactic = AttackTactic(name=name)

        tactic.url = result['fullurl']
        tactic.description = result['printouts']['Has description'][0]
        tactic.save()

        tactics[tactic.name] = tactic

    params['query'] = """
        [[Category:Technique]]
        |?Has tactic
        |?Has ID
        |?Has display name
        |?Has technical description
        |limit=9999
    """

    technique_results = requests.get("{}/{}".format(attack_url, 'api.php'), proxies=proxies, params=params, verify=False).json()
    for page, result in technique_results['query']['results'].items():
        technique_id = result['printouts']['Has ID'][0]
        technique = AttackTechnique.objects(technique_id=technique_id).first()

        if technique is None:
            technique = AttackTechnique(technique_id=technique_id)

        technique.name = result['printouts']['Has display name'][0]
        technique.url = result['fullurl']
        technique.tactics = [tactics[_['fulltext']] for _ in result['printouts']['Has tactic']]
        technique.description = result['printouts']['Has technical description'][0]
        technique.save()
