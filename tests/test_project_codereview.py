#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool

from trytond.modules.company.tests import create_company, set_company


class CodeReviewTestCase(ModuleTestCase):
    'Test module'
    module = 'project_codereview'

    @with_transaction()
    def test0010_components(self):
        'Codereview components should be copied to tasks'
        pool = Pool()
        ProjectWork = pool.get('project.work')
        Component = pool.get('project.work.component')
        ComponentCategory = pool.get('project.work.component_category')
        Codereview = pool.get('project.work.codereview')

        company = create_company()
        with set_company(company):
            task, = ProjectWork.create([{
                        'name': 'Task 1',
                        'type': 'task',
                        'company': company.id,
                        }])
            category, = ComponentCategory.create([{
                        'name': 'Category',
                        }])
            c1, c2 = Component.create([{
                        'name': 'Component 1',
                        'category': category.id,
                        }, {
                        'name': 'Component 2',
                        }])
            Codereview.create([{
                        'name': 'Review1',
                        'url': 'http://codereview',
                        'review_id': '12',
                        'branch': 'default',
                        'component': c1.id,
                        'work': task.id,
                        }])
            task = ProjectWork(task.id)
            self.assertIn(c1, task.components)
            self.assertIn(category, task.component_categories)
            Codereview.create([{
                        'name': 'Review2',
                        'url': 'http://codereview',
                        'review_id': '12',
                        'branch': 'default',
                        'component': c2.id,
                        'work': task.id,
                        }])
            task = ProjectWork(task.id)
            self.assertIn(c2, task.components)

            task, = ProjectWork.create([{
                        'name': 'Task 2',
                        'type': 'task',
                        'company': company.id,
                        }])
            Codereview.create([{
                        'name': 'Review2',
                        'url': 'http://codereview',
                        'review_id': '12',
                        'branch': 'default',
                        'component': c2.id,
                        'category': category.id,
                        'work': task.id,
                        }])

            task = ProjectWork(task.id)
            self.assertIn(c2, task.components)
            self.assertIn(category, task.component_categories)


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        CodeReviewTestCase))
    return suite
