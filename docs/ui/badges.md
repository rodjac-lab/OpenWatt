# Badge mapping (Spec-Kit)

| data_status | Label (FR) | Tooltip | Color token |
|-------------|------------|---------|-------------|
| `fresh` | Frais | "Observation = 7 jours, validée" | `badgeGreen` |
| `verifying` | Vérification en cours | "Changement détecté, validation TRVE en attente (< 48 h)" | `badgeAmber` |
| `stale` | Obsolète | "Dernière observation > 14 jours" | `badgeGrey` |
| `broken` | En panne | "Parsing en échec ou données rejetées" | `badgeRed` |

Usage notes:
- Always display the tooltip or helper text so contributors understand why a tariff is degraded.
- `verifying` is independent from time; the backend flips it back to `fresh` once TRVE validation passes.
- `broken` rows should trigger UI banners and link to the GitHub alert referenced in the logs.
