# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['ProjectCodeReview', 'Work']


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
            raise UserError(gettext('project_codereview.invalid_work_state',
                    codereview=self.rec_name,
                    work=self.work.rec_name))

    @classmethod
    @ModelView.button
    def open(cls, codereviews):
        cls.write(codereviews, {'state': 'opened'})

    @classmethod
    @ModelView.button
    def done(cls, codereviews):
        cls.write(codereviews, {'state': 'done'})

    @classmethod
    def create(cls, values):
        pool = Pool()
        Category = pool.get('project.work.component_category')
        Component = pool.get('project.work.component')
        Work = pool.get('project.work')
        for value in values:
            task = Work(value.get('work'))
            component = Component(value.get('component'))
            if value.get('category'):
                category = Category(value.get('category'))
                if not category in task.component_categories:
                    task.component_categories += (category,)
                    task.save()
            if component not in task.components:
                task.components += (component),
                if (component.category and
                        component.category not in task.component_categories):
                    task.component_categories += (component.category,)
                task.save()
        return super(ProjectCodeReview, cls).create(values)


class Work(metaclass=PoolMeta):
    __name__ = 'project.work'

    codereview = fields.One2Many('project.work.codereview', 'work',
        'Codereviews', states={
            'invisible': Eval('type') != 'task',
            }, depends=['type'])


    @classmethod
    def write(cls, *args):
        actions = iter(args)
        for works, vals in zip(actions, actions):
            if vals.get('state', '') == 'done':
                for work in works:
                    for codereview in work.codereview:
                        if codereview.state == 'opened':
                            raise UserError(gettext(
                                'project_codereview.invalid_codereview_state',
                                    codereview=codereview.rec_name,
                                    work=work.rec_name))
        super(Work, cls).write(*args)
