# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from sql.operators import Equal
from trytond.model.exceptions import ValidationError
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
                'project_codereview.msg_codereview_url_unique'),
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
            raise ValidationError(gettext('project_codereview.invalid_work_state',
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
        Work = Pool().get('project.work')

        records = super().create(vlist)
        works = list(set(r.work for r in records))
        Work.sync_components_categories(works)
        return records

    @classmethod
    def write(cls, *args):
        Work = Pool().get('project.work')

        records = sum([x for x in args[::2]], [])
        # As the codereview could change from one task to another, we need to
        # sync both the old and the new tasks
        works = list(set(r.work for r in records))
        super().write(*args)
        works += list(set(r.work for r in records))
        Work.sync_components_categories(works)

    @classmethod
    def delete(cls, records):
        Work = Pool().get('project.work')

        works = list(set(r.work for r in records))
        super().delete(records)
        Work.sync_components_categories(works)


class Work(metaclass=PoolMeta):
    __name__ = 'project.work'

    codereviews = fields.One2Many('project.work.codereview', 'work',
        'Codereviews', states={
            'invisible': Eval('type') != 'task',
            })

    @classmethod
    def sync_components_categories(cls, works):
        for work in works:
            components = set()
            categories = set()
            for codereview in work.codereviews:
                components.add(codereview.component)
                if codereview.category:
                    categories.add(codereview.category)
                if codereview.component.category:
                    categories.add(codereview.component.category)
            work.components = list(components)
            work.component_categories = list(categories)
        cls.save(works)

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
                raise ValidationError(gettext(
                    'project_codereview.invalid_codereview_state',
                        codereview=codereview.rec_name,
                        work=self.rec_name))
