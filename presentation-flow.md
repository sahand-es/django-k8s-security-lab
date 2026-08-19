# Django Backend Security Training - Pre-CTF Flow

## Context

This document captures the current agreed flow for the third and final session of a 3-session Django backend training for CloudOps interns.

The final blackbox CTF will be designed later. This document only covers everything before that CTF.

## Core Message

Infrastructure security matters, but application bugs can still break assumptions made at the infrastructure layer.

The session should not imply that infrastructure security is useless. The intended message is:

- application security and infrastructure security protect different trust boundaries;
- a privileged backend becomes part of the security boundary;
- infrastructure controls should limit blast radius when an application makes a mistake.

Memorable formulation:

> The application decides what should happen; the infrastructure limits how bad it can get when the application is wrong.

## Time Box

Total time before the final CTF:

- 4 hours total
- includes a 30-minute break
- approximately 3.5 hours of active teaching and exercises

The format should alternate between teaching, live demonstrations, short questions, and whitebox challenges.

## High-Level Narrative

The agreed session arc is:

1. Django provides strong safety rails for several famous web vulnerabilities.
2. Those protections work best when developers use Django in the intended way.
3. Django cannot automatically know business ownership and object-authorization rules.
4. Django also cannot automatically protect every integration boundary.
5. The riskiest later-stage bugs appear when the backend acts as a bridge to more powerful systems: filesystem, shell, outbound HTTP, background workers, and privileged external services.
6. Kubernetes will later be one example of a privileged external system, but the pre-CTF teaching should stay mostly focused on backend security.

Short version:

> Part 1: famous web attacks and what Django protects you from.
>
> Part 2: integration mistakes where Django cannot automatically save you.

## Opening

Purpose:

- Establish the premise.
- Make the session feel practical and backend-oriented.
- Avoid turning the opening into a Kubernetes security lecture.

Key points:

- Teams may invest in TLS, authentication, RBAC, namespaces, NetworkPolicies, admission policies, service mesh, and other infrastructure controls.
- A simple application-level vulnerability can still undermine assumptions made by those controls.
- This does not mean infrastructure security is pointless.
- It means application security and infrastructure security must work together.

Opening framing:

> Today we start with ordinary Django/backend security bugs, then gradually move toward what happens when the backend has privileges the user does not have.

## Teaching Rhythm

For each main vulnerability section:

1. Show normal behavior.
2. Show the vulnerable Django code.
3. Ask: "What does this code trust that it shouldn't?"
4. Let interns predict an attack.
5. Perform the live PoC.
6. Explain why it worked.
7. Show the secure implementation.
8. Extract one memorable security principle.

Avoid framing the session as a vocabulary quiz.

Prefer questions like:

> What does this code trust that it shouldn't?

> Who is allowed to choose this value?

> Is this value data, code, a path, a URL, or an action?

> Is the backend doing something with its own authority here?

## Part 1: Famous Web Attacks And Django's Built-In Defenses

Theme:

> Django gives you strong safety rails, as long as you stay on them.

Part 1 should focus on famous, beginner-friendly web vulnerabilities where Django has recognizable built-in protections.

### 1. SQL Injection

Core idea:

- SQL injection happens when user input becomes part of a database query as code instead of data.

Django safety rail:

- ORM query construction
- parameterized queries

Demo shape:

1. Show a safe ORM search.
2. Show a vulnerable raw/manual SQL query.
3. Exploit it with a simple search payload.
4. Fix it with ORM filtering or parameterized raw SQL.

Principle:

> Keep user input as data, not query code.

### 2. XSS

Core idea:

- XSS happens when user-controlled content becomes executable HTML or JavaScript in another user's browser.

Django safety rail:

- template autoescaping

Demo shape:

1. Show safe rendering in a Django template.
2. Show unsafe rendering with `mark_safe`, `|safe`, or equivalent raw HTML handling.
3. Store or reflect a simple payload.
4. Fix by removing unsafe rendering and treating user content as text.

Principle:

> User content should render as content, not code.

### 3. CSRF

Core idea:

- CSRF happens when a victim's browser is tricked into making a state-changing request using the victim's session.

Django safety rail:

- CSRF middleware
- `{% csrf_token %}`

Demo shape:

1. Show a normal protected POST form.
2. Show a deliberately unsafe state-changing endpoint with CSRF protection removed.
3. Trigger the action from another page.
4. Fix by restoring CSRF protection and keeping state changes behind POST plus token checks.

Principle:

> A logged-in browser is not proof that the user intentionally made the request.

### Short Clarification: CORS

This should come immediately after CSRF.

Do not make this a full live demo unless later timing allows it. The main purpose is to prevent interns from mixing up CSRF and CORS.

Core distinction:

> CSRF asks: "Can another site make the victim's browser send a request with their cookies?"
>
> CORS asks: "Can another site's JavaScript read the response?"

Key points:

- CORS is not CSRF protection.
- Restrictive CORS does not stop a normal HTML form POST.
- Overly broad CORS can expose authenticated API responses to malicious sites.
- Reflecting the `Origin` header is usually a dangerous shortcut.
- `Access-Control-Allow-Credentials: true` needs extra care.

Principle:

> CORS controls who can read responses in the browser; CSRF controls whether state-changing requests require user intent.

### 4. Clickjacking

This should be a short section, not a deep exploit demo.

Core idea:

- Clickjacking tricks a user into interacting with the real application while it is hidden or framed by another site.

Django safety rail:

- `django.middleware.clickjacking.XFrameOptionsMiddleware`
- `X-Frame-Options` response header

Demo shape:

1. Show the protected page.
2. Check the response header.
3. Explain that browser-enforced framing rules reduce this class of UI deception.

Principle:

> Some attacks trick the user into clicking the real app through a malicious frame.

### 5. Open Redirect / Host Trust

Core idea:

- Open redirects happen when the application redirects users to attacker-controlled destinations.
- Host trust bugs happen when the app trusts request host/header values in security-sensitive links or redirects.

Django safety rail:

- `ALLOWED_HOSTS`
- safe redirect helpers and explicit validation
- careful handling of `next` parameters

Demo shape:

1. Show a normal login or post-action redirect.
2. Show unsafe use of `next`.
3. Redirect to an attacker-controlled URL.
4. Fix with allowed-host validation or server-side known redirect destinations.

Principle:

> The user can request where to go next, but the server must decide whether that destination is allowed.

### Short Deployment Security Settings Note

This should be a short end-of-Part-1 note, not a local HTTPS demo.

Cover:

- HTTPS redirect
- secure session cookies
- secure CSRF cookies
- HSTS
- keeping `SECRET_KEY` secret

Principle:

> Django has settings for browser and transport protections, but they only work when deployment matches the assumptions.

## End Of Part 1 Bridge: IDOR / Object Authorization

This should happen at the end of Part 1, without a full live demo.

Purpose:

- Bridge from framework-provided protections into application-specific authorization.
- Make clear that Django authentication is not object authorization.

Short message:

> Django can help with many generic web-security problems, but it cannot infer your business ownership rules.

Tiny code contrast:

```python
document = Document.objects.get(id=document_id)
```

Safer ownership-scoped lookup:

```python
document = get_object_or_404(
    Document,
    id=document_id,
    project__members=request.user,
)
```

Principle:

> Authentication answers "who are you?" Authorization answers "should you access this specific object?"

Use this as a conceptual bridge rather than a dedicated demo slot.

## Whitebox Challenge 1

Purpose:

- Let interns recognize places where developers bypassed Django's normal protections.
- Keep the challenge small and source-code-oriented.

Challenge style:

- Interns have source code.
- They inspect a small Django app.
- They exploit vulnerabilities based on the Part 1 material.
- Each objective should be short and reachable.

Likely objectives:

1. Find and exploit unsafe raw SQL search.
2. Find and exploit unsafe HTML rendering / XSS.
3. Find and exploit a CSRF-exempt state-changing endpoint.
4. Find and exploit an unsafe redirect.
5. Find a small IDOR/object-authorization issue as a bonus or short required flag.

Review:

- Walk through each vulnerable code path.
- Ask what Django protection was bypassed or what business rule was missing.
- Show the secure version.

## Break

30 minutes.

## Part 2: Integration Mistakes

Theme:

> Django protects web boundaries well, but your backend often becomes a bridge to more powerful systems.

Part 2 should focus on vulnerabilities where the danger comes from the backend integrating with external capabilities.

These are not primarily "Django forgot to protect us" bugs. They are bugs where the application gives user input too much influence over a privileged operation.

### 1. Path Traversal / Unsafe File Access

Core idea:

- The backend reads or serves files based on user-controlled names or paths.
- The user should choose from allowed files, not arbitrary filesystem paths.

Example feature:

- download report
- view generated artifact
- support bundle
- log viewer
- backup export

Demo shape:

1. Show normal file download.
2. Show code that joins a base directory with user input.
3. Use traversal input to read a file outside the intended directory.
4. Fix with server-side file records, allowlisted names, path normalization, and root-directory enforcement.

Principle:

> Users choose resources, not filesystem paths.

### 2. Unsafe Subprocess Usage

Core idea:

- The backend calls an external command or operational script with user-controlled input.
- If input crosses into shell syntax or unsafe command arguments, the user may influence the command beyond the intended operation.

Example feature:

- diagnostics command
- report generation
- backup/export tool
- image or document conversion
- local CLI wrapper

Demo shape:

1. Show a useful backend feature that runs a command.
2. Show unsafe command construction.
3. Exploit command injection or argument injection.
4. Fix by avoiding shell execution, passing argument arrays, validating with allowlists, and limiting what the command can do.

Principle:

> Treat command execution as a privilege boundary.

### 3. Unsafe Outbound Fetch / Webhook Validation

Core idea:

- The backend fetches a user-provided URL.
- The backend may reach networks, services, or addresses the user cannot reach directly.

Example feature:

- test webhook
- import from URL
- fetch avatar
- fetch remote config
- validate callback endpoint

Demo shape:

1. Show normal webhook testing or URL import.
2. Show backend fetch code.
3. Use it to access an internal-only local service.
4. Fix with scheme and host allowlists, private-network blocking, redirect handling, timeouts, and egress controls.

Principle:

> A URL fetch is not just input validation; it is network delegation.

### 4. Unsafe Background Job / Task Parameters

Core idea:

- The web request schedules work to happen later.
- The application trusts user-controlled task parameters too much.
- The worker may execute with different timing, different permissions, or less context than the original request.

Example feature:

- export job
- report generation
- retry action
- notification delivery
- project cleanup
- diagnostics task

Demo shape:

1. Show a web endpoint enqueueing a task.
2. Show unsafe task payload construction from request fields.
3. Exploit by changing object IDs, tenant-related values, action-like values, or other internal parameters.
4. Fix by constructing task payloads server-side from authorized objects and re-checking important invariants in the worker.

Principle:

> Background work still needs authorization-aware inputs.

This may be a shorter explanation or challenge-only topic if time gets tight.

### 5. Unsafe Privileged Integration

Core idea:

- A backend feature performs actions in another system using the backend's own permissions.
- The user is allowed to request some version of the action.
- The bug is that the application does not tightly define what action may be taken or what target it may apply to.

Keep this general during the teaching round.

Possible external systems:

- deployment platform
- cloud API
- internal admin service
- Kubernetes API
- CI/CD system
- database management service
- storage control plane

Conceptual framing:

> The backend is allowed to do something. The user is allowed to request some version of that thing. The bug is that the user can steer the backend outside the intended boundary.

Demo shape:

1. Show a legitimate high-level backend feature.
2. Show that the backend performs the operation through a privileged integration.
3. Show how user-controlled input can steer the action or target.
4. Fix by deriving sensitive fields server-side, using strict allowlists/templates, narrowing backend permissions, and adding infrastructure-level blast-radius controls.

Principle:

> Do not let users freely steer privileged backend integrations.

Kubernetes bridge:

> In the later CTF, Kubernetes will be one example of this category: the backend has legitimate permissions, and the attacker tries to steer how those permissions are used.

## Whitebox Challenge 2

Purpose:

- Let interns inspect and exploit integration mistakes.
- Gradually transition toward the idea of a SaaS/control-plane backend.
- Keep Kubernetes as a possible example of privileged integration, not the entire lesson.

Challenge style:

- Interns have source code.
- The app should look like a small SaaS/control-plane-like Django backend.
- Users can request diagnostics, downloads, imports, jobs, or operational actions.

Likely objectives:

1. Exploit path traversal in a file/report/log download feature.
2. Exploit unsafe subprocess usage in a diagnostics or tooling feature.
3. Exploit SSRF through webhook testing or URL import.
4. Exploit unsafe background task parameters.
5. Exploit unsafe privileged integration in a general external-system wrapper.

Review:

- Walk through what each endpoint allowed the user to influence.
- Identify what authority the backend had in each case.
- Show how to move sensitive decisions server-side.
- Discuss blast-radius controls.

## Defense-In-Depth Points For Part 2 Review

Application-side fixes:

- derive sensitive values server-side;
- use allowlists instead of blocklists where possible;
- bind every action to an authorized object;
- re-check important invariants in background workers;
- avoid shell execution;
- validate outbound fetch destinations;
- store resources as database records instead of raw paths;
- keep privileged integration APIs narrow.

Infrastructure-side blast-radius controls:

- narrow service permissions;
- namespace isolation;
- NetworkPolicies and egress controls;
- admission policies;
- separate workers for risky actions;
- read-only filesystems where possible;
- no real secrets in training environments;
- fake local services only.

Key message:

> Infrastructure cannot decide the business rule for the application, but it can reduce the damage when the application gets the rule wrong.

## Closing Transition To The Later Blackbox CTF

End the pre-CTF material by connecting the pieces:

> You have now seen the ingredients separately: classic web bugs, missing object authorization, and integration bugs where the backend acts with more power than the user has.

Then transition:

> In the final CTF, these ideas will be hidden inside a SaaS-style application running in Kubernetes.

Make clear:

- The CTF is not being designed yet.
- This session prepares the conceptual runway for it.
- Kubernetes should reinforce defense in depth and blast-radius limitation.
- The core lesson remains backend security.

## Current Topic Placement

Part 1 main topics:

1. SQL injection
2. XSS
3. CSRF
4. Short CORS clarification
5. Clickjacking
6. Open redirect / host trust
7. Short deployment security settings note

End of Part 1 bridge:

- IDOR / object authorization, no full demo

Part 2 main topics:

1. Path traversal / unsafe file access
2. Unsafe subprocess usage
3. Unsafe outbound fetch / webhook validation
4. Unsafe background job / task parameters
5. Unsafe privileged integration

## Current Open Decisions

These should be decided in later iterations:

1. Exact timing for each section.
2. Whether background job/task parameter trust gets a full live demo or appears mostly in Challenge 2.
3. Exact demo application structure.
4. Exact flags and objectives for Whitebox Challenge 1.
5. Exact flags and objectives for Whitebox Challenge 2.
6. Whether to use one Django project with multiple apps or separate demo/challenge projects.
7. Local-only environment details.
8. Whether to include a lightweight fake Kubernetes API/service before using any real local cluster.
9. Slide-by-slide outline.
10. Instructor runbook and fallback demo plan.
