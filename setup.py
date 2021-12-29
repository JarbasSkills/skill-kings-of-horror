#!/usr/bin/env python3
from setuptools import setup

# skill_id=package_name:SkillClass
PLUGIN_ENTRY_POINT = 'skill-kings-of-horror.jarbasai=skill_kings_of_horror:KingsofHorrorSkill'

setup(
    # this is the package name that goes on pip
    name='ovos-skill-kings-of-horror',
    version='0.0.1',
    description='ovos kings of horror skill plugin',
    url='https://github.com/JarbasSkills/skill-kings-of-horror',
    author='JarbasAi',
    author_email='jarbasai@mailfence.com',
    license='Apache-2.0',
    package_dir={"skill_kings_of_horror": ""},
    package_data={'skill_kings_of_horror': ['locale/*', 'ui/*']},
    packages=['skill_kings_of_horror'],
    include_package_data=True,
    install_requires=["ovos_workshop~=0.0.5a1"],
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
