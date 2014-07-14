#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_view, test_depends
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction


class TestCase(unittest.TestCase):
    'Test module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('project_codereview')
        self.company = POOL.get('company.company')
        self.timesheet_work = POOL.get('timesheet.work')
        self.project_work = POOL.get('project.work')
        self.component = POOL.get('project.work.component')
        self.component_category = POOL.get('project.work.component_category')
        self.codereview = POOL.get('project.work.codereview')

    def test0005views(self):
        'Test views'
        test_view('project_codereview')

    def test0006depends(self):
        'Test depends'
        test_depends()

    def test0010_components(self):
        'Codereview components should be copied to tasks'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])

            t_work, = self.timesheet_work.create([{
                        'name': 'Work 1',
                        'company': company.id,
                        }])
            task, = self.project_work.create([{
                        'work': t_work.id,
                        'type': 'task',
                        }])
            category, = self.component_category.create([{
                        'name': 'Category',
                        }])
            c1, c2 = self.component.create([{
                        'name': 'Component 1',
                        'category': category.id,
                        }, {
                        'name': 'Component 2',
                        }])
            self.codereview.create([{
                        'name': 'Review1',
                        'url': 'http://codereview',
                        'review_id': '12',
                        'branch': 'default',
                        'component': c1.id,
                        'work': task.id,
                        }])
            task = self.project_work(task.id)
            self.assertIn(c1, task.components)
            self.assertIn(category, task.component_categories)
            self.codereview.create([{
                        'name': 'Review2',
                        'url': 'http://codereview',
                        'review_id': '12',
                        'branch': 'default',
                        'component': c2.id,
                        'work': task.id,
                        }])
            task = self.project_work(task.id)
            self.assertIn(c2, task.components)

            t_work, = self.timesheet_work.create([{
                        'name': 'Work 2',
                        'company': company.id,
                        }])

            task, = self.project_work.create([{
                        'work': t_work.id,
                        'type': 'task',
                        }])
            self.codereview.create([{
                        'name': 'Review2',
                        'url': 'http://codereview',
                        'review_id': '12',
                        'branch': 'default',
                        'component': c2.id,
                        'category': category.id,
                        'work': task.id,
                        }])

            task = self.project_work(task.id)
            self.assertIn(c2, task.components)
            self.assertIn(category, task.component_categories)


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite:
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
