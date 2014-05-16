# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, And

__all__ = ['ProjectCodeReview', 'Work']
__metaclass__ = PoolMeta


class ProjectCodeReview(ModelSQL, ModelView):
    'Project Code Review'
    __name__ = 'project.work.codereview'

    name = fields.Char('Name', required=True, select=True)
    url = fields.Char('Url', required=True)
    work = fields.Many2One('project.work', 'Work',
        required=True, select=True)
    branch = fields.Char('Branch', required=True, select=True)
    category = fields.Many2One('project.work.component_category', 'Category',
        required=False, select=True)
    component = fields.Many2One('project.work.component', 'Component',
        required=True, select=True)
    comment = fields.Text('comment')
    state = fields.Function(fields.Char('State'),
        'get_codereview_state', searcher='search_codereview_state')

    def get_codereview_state(self, name):
        return self.work.state

    @classmethod
    def search_codereview_state(cls, name, clause):
        pool = Pool()
        Work = pool.get('project.work')
        works = Work.search(clause)
        work_ids = [x.id for x in works]
        return [('work', 'in', work_ids)]


class Work:
    __name__ = 'project.work'

    codereview = fields.One2Many('project.work.codereview', 'work',
        'Codereviews', states={
            'invisible': Eval('type') != 'task',
        }, depends=['type'])
