# Playbook Subscription Links

Starting or stopping a Playbook can affect real funds. The agent must never
perform those actions directly. It may only generate a short-lived GetAgent
page link and return that link to the user.

## Start or Subscribe Link

`POST /api/v1/playbook/versions/follow-link`

**Auth**: `ACCESS-KEY` header from the Bitget OpenAPI credential.

```json
{
  "version_id": "version-...",
  "source": "studio"
}
```

The version must be published and eligible for subscription. The response is:

```json
{
  "url": "https://api.bitget.com/api/v1/playbook/links/open?token=...",
  "expires_at": "2026-08-24T12:10:00+00:00",
  "version_id": "version-..."
}
```

Return `url` as a clickable link. Do not open it or claim that the Playbook has
started. The user must review and confirm the action in GetAgent.

## Manage or Stop Link

First use `GET /api/v1/playbook/my-playbooks` to find the active
`instance_id`, then call:

`POST /api/v1/playbook/instances/manage-link`

**Auth**: `ACCESS-KEY` header from the Bitget OpenAPI credential.

```json
{
  "instance_id": "instance-..."
}
```

Return the response `url` as a clickable link. Do not open it and do not claim
that the Playbook stopped. The GetAgent page explains any cancellation or
position-closing effects and requires the user to confirm them.

## Prohibited Calls

Do not call legacy `/api/v1/playbook/enable` or
`/api/v1/playbook/disable` endpoints, product `launch`/`terminate` endpoints,
Trade SDK mutation APIs, or any equivalent lifecycle mutation on the user's
behalf.
