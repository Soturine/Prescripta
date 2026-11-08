# UI/UX e acessibilidade — revisão desta rodada

Escopo real (não exaustivo): jornada de checagem clínica do perfil médico, em navegador Chromium
real via Playwright (desktop 1440×900), com dados sintéticos do seed E2E; card de alternativas em
PT-BR e EN-US (teste de componente); estados de sessão (login, logout, expiração, multi-aba).
Gates automatizados existentes executados a cada checkpoint: axe (dashboard e fluxo clínico),
snapshots visuais `@visual`, EN-US com axe, reflow mobile/tablet, reduced motion — 19 passed /
2 skipped. **Não executado nesta rodada:** leitor de tela real, zoom 200/400 %, revisão por perfil
de farmácia/enfermagem/pesquisa/admin, contraste medido fora do axe.

| ID | Achado (navegador real ou teste) | Impacto | Decisão / mudança | Evidência |
|---|---|---|---|---|
| NEW-11 | Card de alternativas exibia selo verde "Liberado" para candidatos avaliados parcialmente com a dose de outro fármaco | falsa segurança | Selo nunca `liberado`; "Candidato para revisão"; coluna "Dose: Não avaliada"; aviso explícito acima da tabela | `AlternativeMedicationsCard.test.tsx`; snapshot de acessibilidade da página (região rotulada, cabeçalhos de coluna com `scope`) |
| NEW-11 (i18n) | Card em PT fixo mesmo com EN-US selecionado, embora a página pai seja superfície migrada | inconsistência de idioma | Migrado para catálogo; incluído no gate de i18n; enums mapeados para rótulos | gate i18n 877 chaves |
| NEW-20 | Em navegador real, para o analgésico padrão do formulário as "alternativas do mesmo grupo" eram amoxicilina, bupivacaína, bupropiona e carbamazepina (ordem alfabética), porque 29 de 40 cadastros do seed compartilham a classe-marcador "demo pendente de revisão" | sugestão clinicamente absurda apresentada como semelhante | Classe-marcador não conta como semelhança; correspondência por classe tem rótulo próprio ("Mesma classe terapêutica cadastrada"); "mesmo grupo" só para o campo curado. Após o fix, o mesmo fluxo não mostra alternativas (honesto: não há similaridade curada) | `test_placeholder_class_is_not_similarity` (falha no HEAD anterior); recaptura no navegador |
| NEW-14 | `formatDose` arredondava doses pequenas na tela | valor exibido ≠ calculado | sem arredondamento nem separador de milhar | `formatters.test.ts` |
| NEW-16 | Corridas de sessão (login após carregamento lento, logout/login rápidos, multi-aba) | perda de sessão / dados visíveis após logout em outra aba | época de sessão, logout aguardado, `BroadcastChannel` | `AuthContext.test.tsx` |

## Rodada por perfil (CP-K)

Spec `frontend/e2e/profile-accessibility.spec.ts`: cada um dos 8 perfis demo (admin, médico,
enfermagem, auditoria, farmácia, psicologia, safety, pesquisa) entra e percorre as páginas do próprio
menu em Chromium desktop 1440×1000, PT-BR: 59 visitas de página. Em cada uma, axe completo, exatamente
um `h1`, um landmark `main` e nenhuma resposta 403 da API. Bloqueiam: violações serious/critical e as
regras estruturais `heading-order`, `landmark-no-duplicate-main`, `landmark-main-is-top-level`.

Encontrado e corrigido: NEW-27 (dois `main`), NEW-28 (contraste e ordem de cabeçalhos), NEW-29 (403 em
`/protocols` para auditoria e safety). Depois: 0 violações bloqueantes, 0 respostas 403, E2E completo
27 passed / 2 skipped.

Limites desta rodada: só desktop e PT-BR por perfil (mobile, tablet, EN-US e reduced motion seguem
cobertos apenas para o médico); páginas de detalhe (paciente, relatório) só onde o fluxo existente já
passa; **nenhum leitor de tela real** (NVDA, JAWS, VoiceOver) foi usado: axe e estrutura de landmarks
são pré-condição, não prova de usabilidade com tecnologia assistiva. Zoom 200/400 % não executado.

Oportunidades registradas e não implementadas: diferenciar visualmente "severidade do achado" e
"nível agregado" no cabeçalho do resultado (ADR 010) — DEFER; auditoria com leitor de tela —
pendente.
