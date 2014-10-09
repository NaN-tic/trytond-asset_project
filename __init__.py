# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .asset import *
from .configuration import *


def register():
    Pool.register(
        Configuration,
        ConfigurationCompany,
        Project,
        ProjectMilestoneGroup,
        ProjectSaleLine,
        Sale,
        ShipmentWork,
        Maintenance,
        MilestoneGroup,
        module='asset_project', type_='model')
