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
    review_id = fields.Char('Review Id', required=True, select=True)
    branch = fields.Char('Branch', required=True, select=True)
    category = fields.Many2One('project.work.component_category', 'Category',
        required=False, select=True)
    component = fields.Many2One('project.work.component', 'Component',
        required=True, select=True)
    comment = fields.Text('comment')
    state = fields.Selection([
            ('opened', 'Opened'),
            ('done', 'Done'),
            ], 'State', required=True, readonly=True, select=True)

    @classmethod
    def __setup__(cls):
        super(ProjectCodeReview, cls).__setup__()
        cls._error_messages.update({
                'invalid_work_state': ('Code Review "%(codereview)s" can not '
                    'be opened because its work "%(work)s" is already done.'),
                })
        cls._buttons.update({
                'open': {
                    'invisible': Eval('state') == 'opened',
                    },
                'done': {
                    'invisible': Eval('state') == 'done',
                    },
                })

    @staticmethod
    def default_state():
        return 'opened'

    @classmethod
    def validate(cls, codereviews):
        super(ProjectCodeReview, cls).validate(codereviews)
        for codereview in codereviews:
            codereview.check_state()

    def check_state(self):
        if self.state == 'opened' and self.work.state == 'done':
            self.raise_user_error('invalid_work_state', {
                    'codereview': self.rec_name,
                    'work': self.work.rec_name,
                    })

    @classmethod
    @ModelView.button
    def open(cls, codereviews):
        for codereview in codereviews:
            codereview.state = 'opened'
            codereview.save()

    @classmethod
    @ModelView.button
    def done(cls, codereviews):
        for codereview in codereviews:
            codereview.state = 'done'
            codereview.save()


class Work:
    __name__ = 'project.work'

    codereview = fields.One2Many('project.work.codereview', 'work',
        'Codereviews', states={
            'invisible': Eval('type') != 'task',
            }, depends=['type'])

    @classmethod
    def __setup__(cls):
        super(Work, cls).__setup__()
        cls._error_messages.update({
                'invalid_codereview_state': (
                    'Work "%(work)s" can not be set done because its '
                    'codereview "%(codereview)s" is still opened.'),
                })

    @classmethod
    def write(cls, works, vals):
        if vals.get('state', '') == 'done':
            for work in works:
                for codereview in work.codereview:
                    if codereview.state == 'opened':
                        cls.raise_user_error('invalid_codereview_state', {
                                'codereview': codereview.rec_name,
                                'work': work.rec_name,
                                })
        super(Work, cls).write(works, vals)
