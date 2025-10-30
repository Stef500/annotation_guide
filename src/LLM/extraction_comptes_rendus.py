#!/usr/bin/env python3
"""
Script d'extraction d'informations des comptes rendus médicaux
Utilise langextract pour extraire des entités structurées des documents médicaux.
"""

import langextract as lx
import textwrap
import os
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
from dotenv import load_dotenv
from tqdm import tqdm

# Charger les variables d'environnement depuis .env
load_dotenv()


class ExtractionComptesRendus:
    """Classe pour l'extraction d'informations des comptes rendus médicaux"""

    def __init__(self, api_key: str = None):
        """
        Initialise l'extracteur

        Args:
            api_key: Clé API pour le modèle (optionnel si variable d'environnement définie)
        """
        # Charger la clé API depuis .env ou variable d'environnement
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY') or os.environ.get('LANGEXTRACT_API_KEY')
        if not self.api_key:
            raise ValueError("Clé API requise. Définissez OPENAI_API_KEY dans le fichier .env ou comme variable d'environnement")

        # Configuration du prompt et des exemples
        self.setup_extraction_config()

    def setup_extraction_config(self):
        """Configure le prompt et les exemples pour l'extraction médicale spécialisée"""

        # Prompt spécialisé pour l'extraction de concepts médicaux dans les bactériémies
        self.prompt_description = textwrap.dedent("""
        Extraire les concepts médicaux spécialisés des comptes rendus d'hospitalisation.

        CONCEPTS À EXTRAIRE (dans l'ordre d'apparition) :
        1. BACTÉRIÉMIE : bactériémie, hémoculture, septicémie
        2. BACTÉRIE : Noms de bactéries avec toutes leurs variantes (S. aureus, Staphylococcus aureus, Staph doré, etc.)
        3. RÉSISTANCE : résistant à la méthicilline, sauvage, BLSE, PLP2a, sensible, résistant
        4. SITE PRIMAIRE : Point de départ de l'infection (urines, digestif, poumon, cathéter, etc.)
        5. SITE SECONDAIRE : Complications infectieuses (embole septique, greffe sur cathéter, etc.)
        6. INFECTION :  Description du foyer infectieux (abcès, péritonite, infection prostatique, PNA, etc.)

        RÈGLES IMPORTANTES :
        - Extraire le texte EXACT sans paraphrase
        - Identifier une infection uniquement si bactériémie/bactérie mentionnée dans le contexte
        - Marquer les négations qui invalident un concept pour justifier la suppression d’une information.
        - Utiliser les attributs (uniquement si applicable) pour préciser sous-concepts et relations
        - Respecter la hiérarchie Site>Site primaire/secondaire
        """)

        # Exemples d'entraînement basés sur la terminologie médicale spécialisée des bactériémies
        self.examples = [
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Patient admis pour bactériémie à S. aureus résistant à la méthicilline.
                Point de départ probablement sur cathéter veineux central.
                Compliquée par un embole septique au niveau pulmonaire.
                Hémocultures positives à Staphylococcus aureus.
                Absence d'argument en faveur d'une endocardite.
                """),
                extractions=[
                    lx.data.Extraction(
                        extraction_class="bacteriemie",
                        extraction_text="bactériémie"
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="S. aureus",
                        attributes={
                            "nom_complet": "Staphylococcus aureus",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="resistance",
                        extraction_text="résistant à la méthicilline",
                    ),
                    lx.data.Extraction(
                        extraction_class="site_primaire",
                        extraction_text="cathéter veineux central",
                        attributes={
                            "type": "cathéter",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="site_secondaire",
                        extraction_text="embole septique au niveau pulmonaire",
                        attributes={
                            "type": "complication",
                            "localisation": "poumon",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacteriemie",
                        extraction_text="Hémocultures positives",
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="Staphylococcus aureus",
                        attributes={
                            "nom_complet": "Staphylococcus aureus",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="infection",
                        extraction_text="endocardite"
                    )
                ]
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Infection urinaire compliquée sur foyer rénal à E. coli BLSE.
                Les hémocultures ne révèlent pas de bactériémie associée.
                Abcès au niveau du rein droit documenté par scanner.
                Escherichia coli sensible aux carbapénèmes.
                """),
                extractions=[
                    lx.data.Extraction(
                        extraction_class="infection",
                        extraction_text="Infection urinaire"
                    ),
                    lx.data.Extraction(
                        extraction_class="site_primaire",
                        extraction_text="rein",
                        attributes={
                            "localisation": "rein"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="E. coli",
                        attributes={
                            "nom_complet": "Escherichia coli",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="resistance",
                        extraction_text="BLSE",
                        attributes={
                            "profil": "résistant_béta_lactamines"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacteriemie",
                        extraction_text="bactériémie associée"
                    ),
                    lx.data.Extraction(
                        extraction_class="infection",
                        extraction_text="Abcès au niveau du rein droit",
                        attributes={
                            "forme": "abcès",
                            "localisation": "rein_droit",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="Escherichia coli",
                        attributes={
                            "nom_complet": "Escherichia coli",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="resistance",
                        extraction_text="sensible aux carbapénèmes",
                        attributes={
                            "profil": "sensible"
                        }
                    )
                ]
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                                Septicémie à point de départ urinaire à E. Cloacae BLSE et 
                                Pseudomonas aeruginosa traité par Tazocilline.
                                """),
                extractions=[
                    lx.data.Extraction(
                        extraction_class="bacteriemie",
                        extraction_text="Septicémie",
                    ),
                    lx.data.Extraction(
                        extraction_class="site_primaire",
                        extraction_text="à point de départ urinaire",
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="E. Cloacae",
                        attributes={
                            "nom_complet": "Enterobacter cloacae",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="resistance",
                        extraction_text="BLSE",
                        attributes={
                            "profil": "résistant_béta_lactamines"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="Pseudomonas aeruginosa",
                        attributes={
                            "nom_complet": "Enterobacter cloacae",
                        },
                    ),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                        Septicémie à Staphylococcus Epidermidis méti-R taitée par vancomycine.
                        """),
                extractions=[
                    lx.data.Extraction(
                        extraction_class="bacteriemie",
                        extraction_text="Septicémie",
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="Staphylococcus Epidermidis",
                        attributes={
                            "nom_complet": "Staphylococcus epidermidis",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="resistance",
                        extraction_text="méti-R",
                        attributes={
                            "profil": "résistant_methicilline"
                        }
                    ),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Pneumonie à Pneumocoque compliquée de bactériémie.
                Streptococcus pneumoniae isolé dans les crachats et hémocultures.
                Souche sauvage sensible à la pénicilline.
                L'évolution a écarté une méningite associée.
                """),
                extractions=[
                    lx.data.Extraction(
                        extraction_class="infection",
                        extraction_text="Pneumonie",
                        attributes={
                            "type": "poumon"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="Pneumocoque",
                        attributes={
                            "nom_complet": "Streptococcus pneumoniae",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacteriemie",
                        extraction_text="bactériémie",
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="Streptococcus pneumoniae",
                        attributes={
                            "nom_complet": "Streptococcus pneumoniae",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="site_primaire",
                        extraction_text="crachats",
                        attributes={
                            "type": "poumon",
                            "prélèvement": "expectoration",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacteriemie",
                        extraction_text="hémocultures",
                        attributes={
                            "méthode": "hémoculture",
                            "statut": "positive"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="resistance",
                        extraction_text="Souche sauvage",
                        attributes={
                            "profil": "sauvage",
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="resistance",
                        extraction_text="sensible à la pénicilline",
                        attributes={
                            "profil": "sensible"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="infection",
                        extraction_text="méningite associée",
                    )
                ]
            )
        ]

        more_examples = [
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Pneumonie à Haemophilus influenzae d’évolution favorable sous amoxicilline.
                Les hémocultures sont revenues positives.
                Absence de localisation secondaire détectée.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Pneumonie",
                                       attributes={"type": "poumon"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Haemophilus influenzae",
                                       attributes={"nom_complet": "Haemophilus influenzae"}),
                    lx.data.Extraction(extraction_class="bacteriemie", extraction_text="hémocultures",
                                       attributes={"méthode": "hémoculture", "statut": "positif"}),
                    lx.data.Extraction(extraction_class="site_secondaire", extraction_text="localisation secondaire",
                                       attributes={"type": "extension", "statut": "absente"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Pyélonéphrite aiguë à Klebsiella pneumoniae BLSE.
                Bactériémie associée documentée sur deux hémocultures positives.
                Traitée efficacement par imipénème.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Pyélonéphrite aiguë",
                                       attributes={"type": "rein"}),
                    lx.data.Extraction(extraction_class="site_primaire", extraction_text="rein",
                                       attributes={"localisation": "rénal"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Klebsiella pneumoniae",
                                       attributes={"nom_complet": "Klebsiella pneumoniae"}),
                    lx.data.Extraction(extraction_class="resistance", extraction_text="BLSE",
                                       attributes={"profil": "résistant_béta_lactamines"}),
                    lx.data.Extraction(extraction_class="bacteriemie", extraction_text="hémocultures positives",
                                       attributes={"méthode": "hémoculture", "statut": "positive"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Endocardite sur valve native à Enterococcus faecalis.
                Point de départ urinaire probable.
                Traitement par ampicilline et gentamicine avec bonne évolution.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Endocardite",
                                       attributes={"type": "cardiaque"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Enterococcus faecalis",
                                       attributes={"nom_complet": "Enterococcus faecalis"}),
                    lx.data.Extraction(extraction_class="site_primaire", extraction_text="point de départ urinaire",
                                       attributes={"localisation": "urinaire"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Septicémie à Pseudomonas aeruginosa chez un patient porteur de KTC.
                Greffe bactérienne sur cathéter confirmée.
                Retrait du dispositif et traitement par ceftazidime.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="bacteriemie", extraction_text="Septicémie"),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Pseudomonas aeruginosa",
                                       attributes={"nom_complet": "Pseudomonas aeruginosa"}),
                    lx.data.Extraction(extraction_class="site_primaire", extraction_text="KTC",
                                       attributes={"type": "cathéter"}),
                    lx.data.Extraction(extraction_class="infection", extraction_text="greffe bactérienne sur cathéter",
                                       attributes={"type": "dispositif"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Infection de prothèse de hanche à Staphylococcus epidermidis méti-R.
                Présence d’un biofilm suspecté sur la prothèse.
                Traitement chirurgical et vancomycine instaurés.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Infection de prothèse",
                                       attributes={"type": "ostéo-articulaire"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Staphylococcus epidermidis",
                                       attributes={"nom_complet": "Staphylococcus epidermidis"}),
                    lx.data.Extraction(extraction_class="resistance", extraction_text="méti-R",
                                       attributes={"profil": "résistant_methicilline"}),
                    lx.data.Extraction(extraction_class="site_primaire", extraction_text="prothèse de hanche",
                                       attributes={"localisation": "articulaire"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Péritonite biliaire à Escherichia coli et Enterococcus faecium.
                Drainage chirurgical réalisé en urgence.
                Germes sensibles aux carbapénèmes.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Péritonite biliaire",
                                       attributes={"type": "intra-abdominal"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Escherichia coli",
                                       attributes={"nom_complet": "Escherichia coli"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Enterococcus faecium",
                                       attributes={"nom_complet": "Enterococcus faecium"}),
                    lx.data.Extraction(extraction_class="resistance", extraction_text="sensibles aux carbapénèmes",
                                       attributes={"profil": "sensible"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Méningite bactérienne à Neisseria meningitidis sérogroupe B.
                Bactériémie associée sur hémocultures positives.
                Évolution favorable sous céfotaxime.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Méningite",
                                       attributes={"type": "méningée"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Neisseria meningitidis",
                                       attributes={"nom_complet": "Neisseria meningitidis"}),
                    lx.data.Extraction(extraction_class="bacteriemie", extraction_text="hémocultures positives",
                                       attributes={"méthode": "hémoculture", "statut": "positive"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Ostéite du tibia à Staphylococcus aureus sensible à la méticilline.
                Point de départ cutané après plaie traumatique.
                Traitement prolongé par oxacilline IV.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Ostéite",
                                       attributes={"type": "osseux"}),
                    lx.data.Extraction(extraction_class="site_primaire", extraction_text="point de départ cutané",
                                       attributes={"localisation": "peau"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Staphylococcus aureus",
                                       attributes={"nom_complet": "Staphylococcus aureus"}),
                    lx.data.Extraction(extraction_class="resistance", extraction_text="sensible à la méticilline",
                                       attributes={"profil": "sensible"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Abcès hépatique à Klebsiella variicola.
                Drainage échoguidé réalisé avec succès.
                Souche BLSE, traitée par méronem.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Abcès hépatique",
                                       attributes={"forme": "abcès", "localisation": "foie"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Klebsiella variicola",
                                       attributes={"nom_complet": "Klebsiella variicola"}),
                    lx.data.Extraction(extraction_class="resistance", extraction_text="BLSE",
                                       attributes={"profil": "résistant_béta_lactamines"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Bactériémie à Streptococcus gallolyticus d’origine colique.
                Coloscopie ayant révélé un adénocarcinome colique.
                Traitement associant ceftriaxone et chirurgie.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="bacteriemie", extraction_text="Bactériémie"),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Streptococcus gallolyticus",
                                       attributes={"nom_complet": "Streptococcus gallolyticus"}),
                    lx.data.Extraction(extraction_class="site_primaire", extraction_text="origine colique",
                                       attributes={"localisation": "côlon"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Sepsis sévère sur angiocholite à Escherichia coli.
                Hémocultures positives à BLSE.
                Traitement adapté après désobstruction biliaire.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Angiocholite",
                                       attributes={"type": "biliaire"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Escherichia coli",
                                       attributes={"nom_complet": "Escherichia coli"}),
                    lx.data.Extraction(extraction_class="resistance", extraction_text="BLSE",
                                       attributes={"profil": "résistant_béta_lactamines"}),
                    lx.data.Extraction(extraction_class="bacteriemie", extraction_text="hémocultures positives",
                                       attributes={"méthode": "hémoculture", "statut": "positive"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Infection pulmonaire à Acinetobacter baumannii multi-résistant.
                Survenue en réanimation après ventilation prolongée.
                Traitée par colistine et tigécycline.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Infection pulmonaire",
                                       attributes={"type": "poumon"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Acinetobacter baumannii",
                                       attributes={"nom_complet": "Acinetobacter baumannii"}),
                    lx.data.Extraction(extraction_class="resistance", extraction_text="multi-résistant",
                                       attributes={"profil": "multirésistant"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Infection urinaire haute à Proteus mirabilis sensible à la ciprofloxacine.
                Absence de bactériémie associée.
                Guérison sous traitement ambulatoire.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Infection urinaire haute",
                                       attributes={"type": "rein"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Proteus mirabilis",
                                       attributes={"nom_complet": "Proteus mirabilis"}),
                    lx.data.Extraction(extraction_class="resistance", extraction_text="sensible à la ciprofloxacine",
                                       attributes={"profil": "sensible"}),
                    lx.data.Extraction(extraction_class="bacteriemie", extraction_text="bactériémie associée",
                                       attributes={"statut": "absente"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Endocardite sur pacemaker à Staphylococcus lugdunensis.
                Présence d’un embole septique pulmonaire.
                Extraction du matériel et traitement par daptomycine.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Endocardite",
                                       attributes={"type": "cardiaque"}),
                    lx.data.Extraction(extraction_class="site_primaire", extraction_text="pacemaker",
                                       attributes={"type": "dispositif"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Staphylococcus lugdunensis",
                                       attributes={"nom_complet": "Staphylococcus lugdunensis"}),
                    lx.data.Extraction(extraction_class="site_secondaire", extraction_text="embole septique pulmonaire",
                                       attributes={"type": "complication", "localisation": "poumon"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Pneumonie nosocomiale à Enterobacter cloacae céphalosporinase déréprimée.
                Survenue au décours d’une ventilation mécanique.
                Traitée par carbapénème.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Pneumonie nosocomiale",
                                       attributes={"type": "poumon"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Enterobacter cloacae",
                                       attributes={"nom_complet": "Enterobacter cloacae"}),
                    lx.data.Extraction(extraction_class="resistance", extraction_text="céphalosporinase déréprimée",
                                       attributes={"profil": "résistance_inductive"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Spondylodiscite à Brucella melitensis.
                Origine digestive suspectée après ingestion de produits laitiers crus.
                Traitement prolongé par doxycycline et rifampicine.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Spondylodiscite",
                                       attributes={"type": "disco-vertébral"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Brucella melitensis",
                                       attributes={"nom_complet": "Brucella melitensis"}),
                    lx.data.Extraction(extraction_class="site_primaire", extraction_text="origine digestive",
                                       attributes={"localisation": "digestif"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Bactériémie à Staphylococcus haemolyticus chez un patient porteur de KT.
                Point de départ intraveineux probable.
                Antibiothérapie par glycopeptides instaurée.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="bacteriemie", extraction_text="Bactériémie"),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Staphylococcus haemolyticus",
                                       attributes={"nom_complet": "Staphylococcus haemolyticus"}),
                    lx.data.Extraction(extraction_class="site_primaire", extraction_text="KT",
                                       attributes={"type": "cathéter"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Septicémie à Serratia marcescens compliquée d’un abcès pulmonaire.
                Souche productrice de bêta-lactamase.
                Traitée par céfépime et drainage.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="bacteriemie", extraction_text="Septicémie"),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Serratia marcescens",
                                       attributes={"nom_complet": "Serratia marcescens"}),
                    lx.data.Extraction(extraction_class="resistance", extraction_text="bêta-lactamase",
                                       attributes={"profil": "production_betalactamase"}),
                    lx.data.Extraction(extraction_class="site_secondaire", extraction_text="abcès pulmonaire",
                                       attributes={"forme": "abcès", "localisation": "poumon"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Infection du pied diabétique à Pseudomonas aeruginosa et Proteus vulgaris.
                Atteinte osseuse secondaire (ostéite métatarsienne).
                Prise en charge chirurgicale et pipéracilline-tazobactam.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Infection du pied diabétique",
                                       attributes={"type": "parties_molles"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Pseudomonas aeruginosa",
                                       attributes={"nom_complet": "Pseudomonas aeruginosa"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Proteus vulgaris",
                                       attributes={"nom_complet": "Proteus vulgaris"}),
                    lx.data.Extraction(extraction_class="site_secondaire", extraction_text="ostéite métatarsienne",
                                       attributes={"type": "atteinte", "localisation": "os"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Méningite post-traumatique à Streptococcus pneumoniae sensible à la pénicilline.
                Porte d’entrée méningée identifiée après fracture de la base du crâne.
                Guérison sous traitement probabiliste adapté.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Méningite",
                                       attributes={"type": "méningée"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Streptococcus pneumoniae",
                                       attributes={"nom_complet": "Streptococcus pneumoniae"}),
                    lx.data.Extraction(extraction_class="resistance", extraction_text="sensible à la pénicilline",
                                       attributes={"profil": "sensible"}),
                    lx.data.Extraction(extraction_class="site_primaire", extraction_text="porte d’entrée méningée",
                                       attributes={"localisation": "méninge"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Cellulite sévère des membres inférieurs à Streptococcus pyogenes.
                Absence d’hémocultures positives.
                Amélioration rapide sous pénicilline G.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Cellulite",
                                       attributes={"type": "cutané"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Streptococcus pyogenes",
                                       attributes={"nom_complet": "Streptococcus pyogenes"}),
                    lx.data.Extraction(extraction_class="bacteriemie", extraction_text="hémocultures",
                                       attributes={"méthode": "hémoculture", "statut": "négative"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Abcès cérébral à Streptococcus anginosus.
                Point de départ dentaire retenu.
                Drainage neurochirurgical et ceftriaxone.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Abcès cérébral",
                                       attributes={"forme": "abcès", "localisation": "cerveau"}),
                    lx.data.Extraction(extraction_class="bacterie", extraction_text="Streptococcus anginosus",
                                       attributes={"nom_complet": "Streptococcus anginosus"}),
                    lx.data.Extraction(extraction_class="site_primaire", extraction_text="point de départ dentaire",
                                       attributes={"localisation": "dentaire"}),
                ],
            ),
            lx.data.ExampleData(
                text=textwrap.dedent("""
                Pneumopathie d’inhalation sur terrain alcoolique à flore mixte.
                Hémocultures négatives.
                Évolution favorable sous amoxicilline-acide clavulanique.
                """),
                extractions=[
                    lx.data.Extraction(extraction_class="infection", extraction_text="Pneumopathie d’inhalation",
                                       attributes={"type": "poumon"}),
                    lx.data.Extraction(extraction_class="bacteriemie", extraction_text="hémocultures",
                                       attributes={"méthode": "hémoculture", "statut": "négative"}),
                ],
            ),
        ]

        self.examples.extend(more_examples)

    def lire_contenu_fichier(self, chemin_fichier: str) -> str:
        """
        Lit le contenu d'un fichier selon son type

        Args:
            chemin_fichier: Chemin vers le fichier

        Returns:
            Contenu textuel du fichier
        """
        chemin = Path(chemin_fichier)
        extension = chemin.suffix.lower()

        try:
            if extension in ['.txt', '.md']:
                # Fichiers texte simples
                with open(chemin_fichier, 'r', encoding='utf-8') as f:
                    return f.read()

            elif extension == '.docx':
                # Fichiers Word - nécessite python-docx
                try:
                    from docx import Document
                    doc = Document(chemin_fichier)
                    contenu = []
                    for paragraph in doc.paragraphs:
                        contenu.append(paragraph.text)
                    return '\n'.join(contenu)
                except ImportError:
                    logger.warning("python-docx non installé, impossible de lire les fichiers .docx")
                    logger.info("Installez avec: uv add python-docx")
                    return ""

            elif extension == '.pdf':
                # Fichiers PDF - nécessite pypdf ou pdfplumber
                try:
                    import pypdf
                    with open(chemin_fichier, 'rb') as f:
                        reader = pypdf.PdfReader(f)
                        contenu = []
                        for page in reader.pages:
                            contenu.append(page.extract_text())
                        return '\n'.join(contenu)
                except ImportError:
                    try:
                        import pdfplumber
                        with pdfplumber.open(chemin_fichier) as pdf:
                            contenu = []
                            for page in pdf.pages:
                                text = page.extract_text()
                                if text:
                                    contenu.append(text)
                            return '\n'.join(contenu)
                    except ImportError:
                        logger.warning("pypdf ou pdfplumber non installé, impossible de lire les fichiers .pdf")
                        logger.info("Installez avec: uv add pypdf ou uv add pdfplumber")
                        return ""

            else:
                logger.warning(f"Type de fichier non supporté : {extension}")
                return ""

        except Exception as e:
            logger.error(f"Erreur lors de la lecture de {chemin_fichier}: {e}")
            return ""

    def extraire_fichier(self, chemin_fichier: str, passes: int = 3) -> lx.data.AnnotatedDocument:
        """
        Extrait les informations d'un fichier

        Args:
            chemin_fichier: Chemin vers le fichier à analyser
            passes: Nombre de passes d'extraction (pour améliorer le rappel)

        Returns:
            Document annoté avec les extractions
        """
        try:
            contenu = self.lire_contenu_fichier(chemin_fichier)

            if not contenu.strip():
                logger.warning(f"Fichier vide ou illisible : {chemin_fichier}")
                # Retourne un document vide mais valide
                return lx.data.AnnotatedDocument(text="", extractions=[])

            logger.info(f"Extraction des informations de {chemin_fichier}...")

            # VERSION API

            result = lx.extract(
                text_or_documents=contenu,
                prompt_description=self.prompt_description,
                examples=self.examples,
                model_id="gpt-4o-mini",  # OU GPT-5-mini
                api_key=self.api_key,
                extraction_passes=passes,  # Passages multiples pour améliorer le rappel
                max_workers=10,  # Traitement parallèle
                max_char_buffer=1000  # Contextes plus petits pour meilleure précision
            )

            # VERSION SERVEUR LOCAL avec SHIMMY (+backend GPU)

            # from langextract.providers.ollama import OllamaLanguageModel
            #
            # model = OllamaLanguageModel(
            #     model_id="registry.ollama.ai/alibayram/medgemma/4b", # alibayram/medgemma:4b
            #     model_url="http://localhost:11435", # 11434 pour Ollama
            #     timeout=180,
            #     # autres kwargs possibles: temperature ...
            #     num_ctx=4096,  # fenêtre de contexte (par défaut la classe met 2048)
            #     max_output_tokens=256,  # mappe vers num_predict
            #     keep_alive=600,  # garde le modèle chargé (sec)
            #     flash_attn=0,  # <- contourne l'assert n_tokens_all <= n_batch
            #     n_batch=4096,  # augmente la rafale autorisée
            #     n_ubatch=512,
            # )
            #
            # result = lx.extract(
            #     text_or_documents=contenu,
            #     prompt_description=self.prompt_description,
            #     examples=self.examples,
            #     model=model,
            #     fence_output=False,
            #     use_schema_constraints=False,
            #     extraction_passes=passes,
            #     max_workers=1,
            #     max_char_buffer=800,
            # )

            logger.success(f"Extraction terminée : {len(result.extractions)} entités trouvées")
            return result

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de {chemin_fichier}: {e}")
            raise

    def extraire_repertoire(self, chemin_repertoire: str, patterns: List[str] = None) -> Dict[str, lx.data.AnnotatedDocument]:
        """
        Extrait les informations de tous les fichiers d'un répertoire

        Args:
            chemin_repertoire: Chemin vers le répertoire
            patterns: Liste des patterns de fichiers à traiter (défaut: supports multiples formats)

        Returns:
            Dictionnaire des résultats par fichier
        """
        if patterns is None:
            patterns = ["*.md", "*.txt", "*.docx", "*.pdf"]

        resultats = {}
        chemin = Path(chemin_repertoire)

        if not chemin.exists():
            raise FileNotFoundError(f"Répertoire non trouvé : {chemin_repertoire}")

        # Recherche récursive des fichiers pour tous les patterns
        fichiers = []
        for pattern in patterns:
            fichiers.extend(list(chemin.rglob(pattern)))

        if not fichiers:
            logger.warning(f"Aucun fichier {', '.join(patterns)} trouvé dans {chemin_repertoire}")
            return resultats

        logger.info(f"Traitement de {len(fichiers)} fichiers...")

        # Barre de progression pour l'extraction des entités
        with tqdm(total=len(fichiers), desc="Extraction des entités", unit="fichier") as pbar:
            for fichier in fichiers:
                try:
                    # Mise à jour de la description avec le nom du fichier en cours
                    nom_fichier = Path(fichier).name
                    pbar.set_description(f"Extraction: {nom_fichier}")

                    resultat = self.extraire_fichier(str(fichier))
                    resultats[str(fichier)] = resultat

                    # Mise à jour du postfix avec le nombre d'entités trouvées
                    pbar.set_postfix({"entités": len(resultat.extractions)})

                except Exception as e:
                    pbar.set_postfix({"erreur": str(e)[:30]})
                    logger.warning(f"Erreur pour {fichier}: {e}")

                # Avancer la barre de progression
                pbar.update(1)

        return resultats

    def sauvegarder_resultats(self, resultats: Dict[str, lx.data.AnnotatedDocument],
                             repertoire_sortie: str = "extraction") -> None:
        """
        Sauvegarde les résultats avec organisation par fichier

        Args:
            resultats: Dictionnaire des résultats par fichier
            repertoire_sortie: Répertoire de base pour l'extraction
        """
        if not resultats:
            logger.warning("Aucun résultat à sauvegarder")
            return

        # Création du répertoire principal d'extraction
        repertoire_principal = Path(repertoire_sortie)
        repertoire_principal.mkdir(exist_ok=True)

        logger.info(f"Sauvegarde des résultats dans {repertoire_sortie}/")

        # Traitement de chaque fichier individuellement
        for chemin_fichier, document in resultats.items():
            try:
                # Extraction du nom de fichier sans extension
                fichier_path = Path(chemin_fichier)
                nom_fichier = fichier_path.stem  # Sans extension

                # Création du sous-répertoire pour ce fichier
                sous_repertoire = repertoire_principal / nom_fichier
                sous_repertoire.mkdir(exist_ok=True)

                # Sauvegarde JSONL pour ce fichier uniquement
                fichier_jsonl = f"{nom_fichier}.jsonl"
                chemin_jsonl = sous_repertoire / fichier_jsonl

                # Sauvegarde du document unique
                lx.io.save_annotated_documents(
                    [document],  # Document unique en liste
                    output_name=fichier_jsonl,
                    output_dir=str(sous_repertoire)
                )

                logger.info(f"Résultats sauvegardés : {chemin_jsonl}")

                # Génération de la visualisation HTML pour ce fichier
                try:
                    html_content = lx.visualize(str(chemin_jsonl))
                    fichier_html = sous_repertoire / f"{nom_fichier}.html"

                    with open(fichier_html, "w", encoding='utf-8') as f:
                        if hasattr(html_content, 'data'):
                            f.write(html_content.data)  # Pour Jupyter/Colab
                        else:
                            f.write(html_content)

                    logger.info(f"Visualisation générée : {fichier_html}")

                except Exception as e:
                    logger.warning(f"Erreur lors de la génération de la visualisation pour {nom_fichier}: {e}")

            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde de {chemin_fichier}: {e}")
                continue

        # Sauvegarde globale consolidée (optionnelle)
        try:
            documents_tous = list(resultats.values())
            fichier_global = "extraction_complete.jsonl"
            lx.io.save_annotated_documents(
                documents_tous,
                output_name=fichier_global,
                output_dir=str(repertoire_principal)
            )
            logger.info(f"Extraction consolidée : {repertoire_principal / fichier_global}")

        except Exception as e:
            logger.warning(f"Erreur lors de la sauvegarde consolidée : {e}")

    def analyser_resultats(self, resultats: Dict[str, lx.data.AnnotatedDocument]) -> Dict[str, Any]:
        """
        Analyse statistique des résultats d'extraction

        Args:
            resultats: Dictionnaire des résultats

        Returns:
            Statistiques d'analyse
        """
        if not resultats:
            return {}

        # Compilation des statistiques
        total_extractions = 0
        classes_extraction = {}
        fichiers_par_type = {}

        for fichier, document in resultats.items():
            total_extractions += len(document.extractions)

            # Comptage par classe d'extraction
            for extraction in document.extractions:
                classe = extraction.extraction_class
                classes_extraction[classe] = classes_extraction.get(classe, 0) + 1

        stats = {
            'total_fichiers': len(resultats),
            'total_extractions': total_extractions,
            'moyenne_extractions_par_fichier': total_extractions / len(resultats) if resultats else 0,
            'classes_extraction': dict(sorted(classes_extraction.items(), key=lambda x: x[1], reverse=True)),
            'repartition_fichiers': fichiers_par_type
        }

        return stats

    def afficher_statistiques(self, stats: Dict[str, Any]) -> None:
        """Affiche les statistiques d'analyse"""
        if not stats:
            logger.warning("Aucune statistique disponible")
            return

        print("\n" + "="*60)
        logger.info("STATISTIQUES D'EXTRACTION")
        print("="*60)

        logger.info(f"Fichiers traités : {stats['total_fichiers']}")
        logger.info(f"Total extractions : {stats['total_extractions']}")
        logger.info(f"Moyenne par fichier : {stats['moyenne_extractions_par_fichier']:.1f}")

        logger.info("RÉPARTITION PAR CLASSE :")
        for classe, nombre in stats['classes_extraction'].items():
            pourcentage = (nombre / stats['total_extractions']) * 100
            logger.info(f"  • {classe}: {nombre} ({pourcentage:.1f}%)")


def main():
    """Fonction principale"""
    try:
        # Initialisation de l'extracteur
        logger.info("Initialisation de l'extracteur de comptes rendus...")
        extracteur = ExtractionComptesRendus()

        # Répertoire des CR à traiter
        repertoire_exemples = "CR"

        # Vérification de l'existence du répertoire
        if not os.path.exists(repertoire_exemples):
            logger.error(f"Répertoire {repertoire_exemples} non trouvé")

        # Extraction des informations
        logger.info(f"Extraction des fichiers de {repertoire_exemples}...")
        resultats = extracteur.extraire_repertoire(repertoire_exemples)

        if not resultats:
            logger.error("Aucun fichier traité avec succès")
            return

        # Sauvegarde des résultats
        logger.info("Sauvegarde des résultats...")
        extracteur.sauvegarder_resultats(resultats)

        # Analyse statistique
        stats = extracteur.analyser_resultats(resultats)
        extracteur.afficher_statistiques(stats)

        logger.success("Extraction terminée avec succès !")
        logger.info("Structure des résultats :")
        logger.info("  extraction/")
        logger.info("  ├── nom_fichier1/")
        logger.info("  │   ├── nom_fichier1.jsonl")
        logger.info("  │   └── nom_fichier1.html")
        logger.info("  ├── nom_fichier2/")
        logger.info("  │   ├── nom_fichier2.jsonl")
        logger.info("  │   └── nom_fichier2.html")
        logger.info("  └── extraction_complete.jsonl  (consolidé)")
        logger.info("Ouvrez les fichiers .html pour visualiser les extractions par fichier")

    except Exception as e:
        logger.error(f"Erreur dans le processus principal : {e}")
        raise


if __name__ == "__main__":
    main()