# 🏗️ Build Modes Documentation

Ce guide explique comment contrôler la génération de la version finale vs. draft du PDF d'annotation.

## 🎯 Modes de build disponibles

### 🚧 Mode Draft (par défaut)
- **Utilisation** : Développement et tests rapides
- **Caractéristiques** :
  - Compilation rapide
  - Images remplacées par des boîtes placeholder
  - Hyperliens désactivés
  - Tests de pipeline inclus

### ✨ Mode Final 
- **Utilisation** : Version de production
- **Caractéristiques** :
  - Compilation complète avec toutes les optimisations
  - Images haute résolution
  - Hyperliens actifs
  - Pas de tests de pipeline (build direct)

## 🚀 Comment déclencher le mode Final

### 1. Via message de commit (Nouveau!) 
```bash
# Déclenche automatiquement le mode final
git commit -m "[FINAL] - Finalisation chapitre 3 avec exemples EZAnnot"
git push
```

### 2. Via GitHub Release
```bash
git tag v1.0.0
git push origin v1.0.0
# Ou créer une release via l'interface GitHub
```

### 3. Via déclenchement manuel
1. Aller dans **Actions** → **Build PDF** 
2. **Run workflow** → Sélectionner **"final"**

## 📋 Logique de priorité

Le système détermine le mode selon cette logique (par ordre de priorité) :

1. **Manuel** : Paramètre sélectionné dans l'interface GitHub Actions
2. **Release** : Mode final automatique lors de la création d'une release
3. **Message de commit** : Mode final si `[FINAL]` détecté dans le message
4. **Défaut** : Mode draft

## 🔍 Vérification du mode

Le workflow affiche clairement le mode détecté :
```
🔍 Build Mode Detection:
  Commit Message: [FINAL] - Finalisation chapitre 3
  Event Type: push
  Manual Input: 
  Final BUILD_TYPE: final

✨ FINAL MODE ACTIVATED - Full production build
```

## 📝 Exemples d'usage

### Messages de commit qui déclenchent le mode final :
```bash
git commit -m "[FINAL] - Version 1.0 du guide complet"
git commit -m "[FINAL] - Corrections finales avant livraison"  
git commit -m "[FINAL] - Mise à jour des exemples BactHub"
```

### Messages de commit en mode draft (défaut) :
```bash
git commit -m "Ajout du chapitre 3 - work in progress"
git commit -m "fix: correction typo dans introduction"
git commit -m "WIP: développement section terminologies"
```

## 🔧 Configuration technique

La logique de détection est implémentée dans `.github/workflows/build-pdf.yml` :

```yaml
BUILD_TYPE: ${{ github.event.inputs.build_type || 
                (github.event_name == 'release' && 'final' || 
                (contains(github.event.head_commit.message, '[FINAL]') && 'final' || 'draft')) }}
```

## 📊 Différences de performance

| Aspect | Draft | Final |
|--------|-------|-------|
| Temps de build | ~2 min | ~4 min |
| Tests pipeline | ✅ Oui | ❌ Non |
| Images | 📦 Placeholder | 🖼️ Haute résolution |
| Hyperliens | ❌ Désactivés | ✅ Actifs |
| Nettoyage cache | ❌ Non | ✅ Oui |

## 💡 Bonnes pratiques

- **Développement** : Utilisez le mode draft par défaut
- **Révision** : Utilisez `[FINAL]` pour les versions à réviser
- **Production** : Créez une release GitHub pour archivage
- **Debug** : Les logs de build sont toujours disponibles en artefacts