<!--
title: '📡 DISPATCHES, September 2026'
description: 'Every dispatch the workflow sent in September 2026, in the order it sent them, each with its source and license.'
tags: [dispatches, generated, 2026, september]
category: dispatches
-->

<!-- markdownlint-disable MD041 -->

<div align="center">

# 📡 DISPATCHES, SEPTEMBER 2026

<a name="top"></a>

**One dispatch per commit, sent at a moment nobody scheduled.**

_Appended, never rewritten._

</div>

---

## Sunday, September 20, 2026

<a name="dispatch-20260920-183803"></a>

### 🚨 GHSA-c8w2-fgvx-vhv4: github.com/kcp-dev/kcp

`security(advisory)` · 18:38 EDT

github.com/kcp-dev/kcp (go) carries a critical severity advisory, 2 days
ago. kcp front-proxy does not strip inbound X-Remote-* identity headers,
allowing any authenticated client to inject groups/warrants and
impersonate system:masters in any workspace. Affected: &lt; 0.31.4. Tracked
as CVE-2026-61682.

_[GitHub Security Advisories](https://github.com/advisories/GHSA-c8w2-fgvx-vhv4) · Advisory metadata, reported as fact_

---
<a name="dispatch-20260920-184118"></a>

### 📚 RFC 9792: Prefix Flag Extension for OSPFv2 and OSPFv3

`docs(rfc)` · 18:41 EDT

June 2025, status proposed standard.

Each OSPF prefix can be advertised with an 8-bit field to indicate
specific properties of that prefix. However, all the OSPFv3 Prefix
Options bits have already been assigned, and only a few bits remain
unassigned in the Flags field of the OSPFv2 Extended Prefix TLV.

 This document solves this problem by defining a variable-length Prefix
Extended Flags sub-TLV for OSPF. This sub-TLV is applicable to OSPFv2
and OSPFv3.

_[RFC Editor](https://www.rfc-editor.org/rfc/rfc9792) · R. Chen, D. Zhao, P. Psenak, K. Talaulikar, L. Gong · IETF Trust Legal Provisions; RFCs may be freely reproduced_

---
