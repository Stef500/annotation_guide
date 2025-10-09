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
        3. RÉSISTANCE : résistant à la méthicilline, sauvage, BLSE, [Positif]PLP2a, sensible, résistant
        4. SITE PRIMAIRE : Point de départ de l'infection (urines, digestif, poumon, cathéter, etc.)
        5. SITE SECONDAIRE : Complications infectieuses (embole septique, greffe sur cathéter, etc.)
        6. INFECTION : Types d'infections (abcès, péritonite, infection prostatique, PNA, etc.)
        7. NÉGATION : Termes de négation (absence d'argument, a écarté, ne révèlent pas, etc.)

        RÈGLES IMPORTANTES :
        - Extraire le texte EXACT sans paraphrase
        - Identifier une infection uniquement si bactériémie/bactérie mentionnée dans le contexte
        - Marquer les négations qui invalident un concept
        - Utiliser les attributs pour préciser sous-concepts et relations
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
                        extraction_text="bactériémie",
                        attributes={
                            "type": "infection_sanguine",
                            "contexte": "admission"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="S. aureus",
                        attributes={
                            "nom_complet": "Staphylococcus aureus",
                            "type": "cocci_gram_positif",
                            "variante": "abrégé"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="resistance",
                        extraction_text="résistant à la méthicilline",
                        attributes={
                            "type": "SARM",
                            "antibiotique": "méthicilline",
                            "profil": "résistant"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="site_primaire",
                        extraction_text="cathéter veineux central",
                        attributes={
                            "type": "cathéter",
                            "localisation": "central",
                            "certitude": "probable"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="site_secondaire",
                        extraction_text="embole septique au niveau pulmonaire",
                        attributes={
                            "type": "complication",
                            "localisation": "poumon",
                            "mécanisme": "embole_septique"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacteriemie",
                        extraction_text="Hémocultures positives",
                        attributes={
                            "type": "diagnostic",
                            "résultat": "positif",
                            "méthode": "hémoculture"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="Staphylococcus aureus",
                        attributes={
                            "nom_complet": "Staphylococcus aureus",
                            "type": "cocci_gram_positif",
                            "variante": "complet"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="negation",
                        extraction_text="Absence d'argument en faveur",
                        attributes={
                            "type": "négation_médicale",
                            "concept_nié": "endocardite",
                            "force": "forte"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="infection",
                        extraction_text="endocardite",
                        attributes={
                            "type": "cardio_vasc",
                            "statut": "écartée",
                            "relation_bacteriemie": "complication_recherchée"
                        }
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
                        extraction_text="Infection urinaire",
                        attributes={
                            "type": "urines",
                            "sévérité": "compliquée",
                            "localisation": "rein"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="site_primaire",
                        extraction_text="foyer rénal",
                        attributes={
                            "type": "urines",
                            "localisation": "rein",
                            "rôle": "point_de_départ"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="E. coli",
                        attributes={
                            "nom_complet": "Escherichia coli",
                            "type": "entérobactérie",
                            "variante": "abrégé"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="resistance",
                        extraction_text="BLSE",
                        attributes={
                            "type": "béta_lactamase_spectre_étendu",
                            "mécanisme": "enzymatique",
                            "profil": "résistant_béta_lactamines"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="negation",
                        extraction_text="ne révèlent pas",
                        attributes={
                            "type": "négation_résultat",
                            "concept_nié": "bactériémie",
                            "force": "forte"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacteriemie",
                        extraction_text="bactériémie associée",
                        attributes={
                            "type": "complication_recherchée",
                            "statut": "absente",
                            "méthode": "hémocultures"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="infection",
                        extraction_text="Abcès au niveau du rein droit",
                        attributes={
                            "type": "urines",
                            "forme": "abcès",
                            "localisation": "rein_droit",
                            "diagnostic": "scanner"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="Escherichia coli",
                        attributes={
                            "nom_complet": "Escherichia coli",
                            "type": "entérobactérie",
                            "variante": "complet"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="resistance",
                        extraction_text="sensible aux carbapénèmes",
                        attributes={
                            "type": "sensibilité",
                            "antibiotique": "carbapénèmes",
                            "profil": "sensible"
                        }
                    )
                ]
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
                            "type": "poumon",
                            "localisation": "parenchyme_pulmonaire",
                            "sévérité": "compliquée"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="Pneumocoque",
                        attributes={
                            "nom_complet": "Streptococcus pneumoniae",
                            "type": "streptocoque",
                            "variante": "nom_usuel"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacteriemie",
                        extraction_text="bactériémie",
                        attributes={
                            "type": "complication",
                            "relation": "pneumonie_compliquée",
                            "statut": "confirmée"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacterie",
                        extraction_text="Streptococcus pneumoniae",
                        attributes={
                            "nom_complet": "Streptococcus pneumoniae",
                            "type": "streptocoque",
                            "variante": "complet"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="site_primaire",
                        extraction_text="crachats",
                        attributes={
                            "type": "poumon",
                            "prélèvement": "expectoration",
                            "rôle": "diagnostic"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="bacteriemie",
                        extraction_text="hémocultures",
                        attributes={
                            "type": "diagnostic",
                            "méthode": "hémoculture",
                            "statut": "positive"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="resistance",
                        extraction_text="Souche sauvage",
                        attributes={
                            "type": "sensibilité_naturelle",
                            "profil": "sauvage",
                            "absence_résistance": "true"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="resistance",
                        extraction_text="sensible à la pénicilline",
                        attributes={
                            "type": "sensibilité",
                            "antibiotique": "pénicilline",
                            "profil": "sensible"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="negation",
                        extraction_text="a écarté",
                        attributes={
                            "type": "négation_évolution",
                            "concept_nié": "méningite",
                            "force": "forte"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="infection",
                        extraction_text="méningite associée",
                        attributes={
                            "type": "SNC",
                            "relation": "complication_recherchée",
                            "statut": "écartée"
                        }
                    )
                ]
            )
        ]

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

    def extraire_fichier(self, chemin_fichier: str, passes: int = 2) -> lx.data.AnnotatedDocument:
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

            result = lx.extract(
                text_or_documents=contenu,
                prompt_description=self.prompt_description,
                examples=self.examples,
                model_id="gpt-4o-mini",  # GPT-4o-mini pour l'équilibre performance/coût
                api_key=self.api_key,
                extraction_passes=passes,  # Passages multiples pour améliorer le rappel
                max_workers=10,  # Traitement parallèle
                max_char_buffer=2000  # Contextes plus petits pour meilleure précision
            )

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