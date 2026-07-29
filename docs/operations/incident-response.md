# Resposta a incidentes

## Classificação

- **SEV-1:** exposição provável de dado/segredo, alteração de decisão clínica, tenant escape ou perda
  extensa de disponibilidade/integridade;
- **SEV-2:** controle de segurança degradado, provider comprometido, restauração falha ou abuso
  localizado;
- **SEV-3:** vulnerabilidade sem exploração conhecida, alerta de dependência ou falha operacional
  contida.

## Fluxo

1. Registre horário, relator, ambiente, versão/SHA e sintomas sem copiar dado sensível.
2. Contenha: desative provider/egress ou credencial afetada, revogue sessões na borda, preserve banco
   e logs; não apague evidência.
3. Avalie escopo por instituição, objeto, período, ações, snapshots e hashes.
4. Rotacione segredos no secret manager; nunca reutilize valor exposto.
5. Corrija em ambiente isolado, execute testes clínicos/segurança/migration e revisão independente.
6. Restaure de backup validado quando integridade não puder ser demonstrada.
7. Comunique responsáveis institucionais, segurança, DPO/jurídico e autoridades conforme obrigação
   aplicável. O repositório não determina prazo legal.
8. Documente causa raiz, timeline, impacto, decisão de notificação, ações e risco residual.

## Evidência mínima

- IDs pseudonimizados de eventos e correlação;
- SHAs, imagens, lockfiles e SBOM;
- migration head, hash de snapshots/arquivos e resultado de restauração;
- configurações relevantes sem valores secretos;
- resultado de CodeQL/SCA/secret scan e logs seguros.

## Contatos

Vulnerabilidade no projeto deve seguir [SECURITY.md](../../SECURITY.md). Incidente de uma implantação
real deve usar os contatos, plantão, DPO e cadeia de escalonamento definidos pela organização; eles não
são inventados neste template.

## Pós-incidente

Atualize threat model, hazard log, testes, runbooks, retenção e treinamento. Reabra o serviço somente
quando integridade, autorização, migrations e rollback estiverem verificados. Não trate ausência de
evidência como evidência de ausência.
