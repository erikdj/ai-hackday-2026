import copy
import unittest
from hallway.common.brief import Brief,digest
from hallway.tests.test_spine import BASIC
from hallway.demo import verified_graph_receipt

class DemoEvidenceTests(unittest.TestCase):
    def evidence(self):
        brief=Brief.model_validate(BASIC).model_dump();hashed=digest(brief)
        checkpoint={'kind':'BOUNDARY_SENT','case_id':'case','approved_room_id':'boundary','revision':1,'digest':hashed}
        approval={'kind':'APPROVAL','scope':'approved_room','case_id':'case','approved_room_id':'boundary','revision':1,'digest':hashed,'brief':brief,'manifest':[]}
        receipt={'kind':'GRAPH_WRITTEN','status':'GRAPH_WRITTEN','case_id':'case','approved_room_id':'boundary','revision':1,'digest':hashed,'who_saw_identifiers':[]}
        return [checkpoint],[approval,receipt]
    def test_accepts_real_matching_receipt_with_actual_empty_query(self):
        case,boundary=self.evidence()
        self.assertEqual(verified_graph_receipt(case,boundary,'case','boundary')['status'],'GRAPH_WRITTEN')
    def test_mock_or_missing_graph_does_not_pass(self):
        case,boundary=self.evidence();boundary[-1]['status']='MOCK_GRAPH_WRITTEN'
        self.assertIsNone(verified_graph_receipt(case,boundary,'case','boundary'))
        self.assertIsNone(verified_graph_receipt(case,boundary[:1],'case','boundary'))
    def test_cross_case_revision_or_missing_lineage_rejected(self):
        case,boundary=self.evidence();case[0]['revision']=2
        with self.assertRaises(ValueError):verified_graph_receipt(case,boundary,'case','boundary')
        case,boundary=self.evidence();del boundary[-1]['who_saw_identifiers']
        with self.assertRaises(ValueError):verified_graph_receipt(case,boundary,'case','boundary')
