# Badge mapping (Spec-Kit)

| data_status | Label (FR)            | Tooltip                                                   | Color token  |
| ----------- | --------------------- | --------------------------------------------------------- | ------------ |
| `fresh`     | Frais                 | "Observation = 7 jours, valid�e"                          | `badgeGreen` |
| `verifying` | V�rification en cours | "Changement d�tect�, validation TRVE en attente (< 48 h)" | `badgeAmber` |
| `stale`     | Obsol�te              | "Derni�re observation > 14 jours"                         | `badgeGrey`  |
| `broken`    | En panne              | "Parsing en �chec ou donn�es rejet�es"                    | `badgeRed`   |

Usage notes:

- Always display the tooltip or helper text so contributors understand why a tariff is degraded.
- `verifying` is independent from time; the backend flips it back to `fresh` once TRVE validation passes.
- `broken` rows should trigger UI banners and link to the GitHub alert referenced in the logs.
