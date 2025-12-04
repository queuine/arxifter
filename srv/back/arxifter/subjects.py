#!/usr/bin/env python

SUBJECTS = [
    "all",
    "animal_behavior_and_cognition",
    "biochemistry",
    "bioengineering",
    "bioinformatics",
    "biophysics",
    "cancer_biology",
    "cell_biology",
    "clinical_trials",
    "developmental_biology",
    "ecology",
    "epidemiology",
    "evolutionary_biology",
    "genetics",
    "genomics",
    "immunology",
    "microbiology",
    "molecular_biology",
    "neuroscience",
    "paleontology",
    "pathology",
    "pharmacology_and_toxicology",
    "physiology",
    "plant_biology",
    "scientific_communication_and_education",
    "synthetic_biology",
    "systems_biology",
    "zoology",
]


def get_subjects():
    return SUBJECTS


def get_subjects_js(func_name):
    return (
        "\n".join([
            ("function " + func_name + "() {"),
            (" " * 4) + "return [",
            ",\n".join(
                (f'{" " * 8}"{item}"' for item in get_subjects())
            ),
            (" " * 4) + "];",
            "}",
        ]) + "\n"
    )


def get_subjects_sh():
    return "\n".join(get_subjects())
