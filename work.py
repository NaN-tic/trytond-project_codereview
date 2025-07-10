# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from sql.operators import Equal
from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.model import Exclude, ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, If


class ProjectCodeReview(ModelSQL, ModelView):
    'Project Code Review'
    __name__ = 'project.work.codereview'

    name = fields.Char('Name', required=True)
    url = fields.Char('Url', required=True)
    work = fields.Many2One('project.work', 'Work',
        required=True)
    review_id = fields.Char('Review Id', required=True)
    branch = fields.Char('Branch', required=True)
    category = fields.Many2One('project.work.component_category', 'Category',
        required=False)
    component = fields.Many2One('project.work.component', 'Component',
        required=True)
    comment = fields.Text('comment')
    state = fields.Selection([
            ('opened', 'Opened'),
            ('done', 'Done'),
            ], 'State', required=True, readonly=True)

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._buttons.update({
                'open': {
                    'invisible': Eval('state') == 'opened',
                    'icon': 'tryton-back',
                    },
                'done': {
                    'invisible': Eval('state') == 'done',
                    'icon': 'tryton-forward',
                    },
                })
        t = cls.__table__()
        cls._sql_constraints += [
            ('url_exclude', Exclude(t, (t.url, Equal),
                    where=(t.state == 'opened')),
                'product.msg_codereview_url_unique'),
            ]

    @staticmethod
    def default_state():
        return 'opened'

    @classmethod
    def view_attributes(cls):
        return super().view_attributes() + [
            ('/tree', 'visual', If(Eval('state') == 'done', 'muted', '')),
            ]

    @classmethod
    def validate(cls, codereviews):
        super(ProjectCodeReview, cls).validate(codereviews)
        for codereview in codereviews:
            codereview.check_state()

    def check_state(self):
        if self.state == 'opened' and self.work.status.progress == 1:
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
    def create(cls, vlist):
        pool = Pool()
        Category = pool.get('project.work.component_category')
        Component = pool.get('project.work.component')
        Work = pool.get('project.work')

        vlist = [x.copy() for x in vlist]
        for values in vlist:
            task = Work(values.get('work'))
            component = Component(values.get('component'))
            if values.get('category'):
                category = Category(values.get('category'))
                if not category in task.component_categories:
                    task.component_categories += (category,)
                    task.save()
            if component not in task.components:
                task.components += (component),
                if (component.category and
                        component.category not in task.component_categories):
                    task.component_categories += (component.category,)
                task.save()
        return super(ProjectCodeReview, cls).create(vlist)


class Work(metaclass=PoolMeta):
    __name__ = 'project.work'

    codereviews = fields.One2Many('project.work.codereview', 'work',
        'Codereviews', states={
            'invisible': Eval('type') != 'task',
            })

    @classmethod
    def validate(cls, works):
        super().validate(works)
        for work in works:
            work.check_codereviews()

    def check_codereviews(self):
        if self.status.progress != 1:
            return
        for codereview in self.codereviews:
            if codereview.state == 'opened':
                raise UserError(gettext(
                    'project_codereview.invalid_codereview_state',
                        codereview=codereview.rec_name,
                        work=self.rec_name))
