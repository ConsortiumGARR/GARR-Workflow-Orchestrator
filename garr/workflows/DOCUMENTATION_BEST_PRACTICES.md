# Documentation Best Practices for Workflow Automation

## Executive Summary

Based on industry research and the **Diátaxis documentation framework**, this document outlines best practices for writing workflow documentation that is clear, actionable, and maintainable.

---

## The Diátaxis Framework

The Diátaxis framework organizes documentation into **four distinct types**, each serving different user needs:

### 1. **Tutorials** (Learning-Oriented)
- **Purpose**: Help newcomers get started and learn the basics
- **When to use**: First-time users who need guided learning
- **Characteristics**:
  - Step-by-step instructions
  - Assumes no prior knowledge
  - Focuses on successful completion
  - Example: "Your First Optical Service Setup"

### 2. **How-To Guides** (Task-Oriented)
- **Purpose**: Help users accomplish specific tasks
- **When to use**: Users know what they want but need instructions
- **Characteristics**:
  - Solution-focused
  - Assumes basic knowledge
  - Direct and practical
  - Example: "How to Modify Service Frequencies"

### 3. **Reference** (Information-Oriented)
- **Purpose**: Provide detailed, authoritative technical information
- **When to use**: Users need to look up specific details
- **Characteristics**:
  - Comprehensive and accurate
  - Structured and consistent
  - No explanations, just facts
  - Example: "API Endpoint Reference", "Parameter Specifications"

### 4. **Explanation** (Understanding-Oriented)
- **Purpose**: Clarify concepts and provide context
- **When to use**: Users want to understand "why"
- **Characteristics**:
  - Conceptual and theoretical
  - Provides context and background
  - Discusses alternatives and trade-offs
  - Example: "Understanding Optical Path Selection", "Why DWDM Grid Compliance Matters"

---

## Best Practices for Workflow Documentation

### 1. **Start with the Inverted Pyramid**

Put the most important information first:

```
1. WHAT IT DOES (1 sentence)
2. CRITICAL IMPACT (traffic/business impact)
3. WHEN TO USE (use cases)
4. QUICK FACTS (time, requirements)
5. DETAILED STEPS
6. TECHNICAL REFERENCE (appendix)
```

**Why**: 80% of users only need the top information; 20% will read everything.

---

### 2. **Use Progressive Disclosure**

Organize content from simple to complex:

- **Level 1**: Executive summary (1-2 paragraphs)
- **Level 2**: Key details and impact (tables, lists)
- **Level 3**: Step-by-step procedures
- **Level 4**: Technical deep-dive (collapsible sections)

**Example Structure**:
```markdown
## Quick Summary
[1-2 sentence overview]

## Impact at a Glance
| What Changes | Impact | Duration |
|--------------|--------|----------|

## Before You Start
[Checklist]

## Procedure
[Steps]

<details>
<summary>Technical Reference</summary>
[Deep technical details]
</details>
```

---

### 3. **Highlight Critical Information**

For operational workflows, users need to know **immediately**:

#### ⚠️ Traffic Impact
- Will this cause an outage?
- How long?
- When does it occur during the workflow?

#### ⏱️ Time Requirements
- Total duration
- Time-sensitive steps

#### ✅ Prerequisites
- What must be in place before starting?
- Required permissions or resources

#### 🔄 Rollback
- Can it be undone?
- How to recover from failures?

**Use visual indicators**:
- ⚠️ Warnings
- ✅ Success criteria
- ❌ Constraints
- 🔄 Reversible actions
- ⏱️ Time-sensitive

---

### 4. **Write for Your Audience**

#### For Network Operators:
- Focus on **what changes on the network**
- Emphasize **traffic impact**
- Include **troubleshooting steps**
- Provide **validation procedures**

#### For Developers:
- Include **technical specifications**
- Document **error handling**
- Reference **API endpoints**
- Show **code examples**

#### For Management:
- Highlight **business impact**
- Show **time/cost estimates**
- Explain **risk factors**

---

### 5. **Structure for Scannability**

People don't read linearly—they scan:

#### Use:
- **Short paragraphs** (3-4 lines max)
- **Bullet points** for lists
- **Tables** for comparisons
- **Bold** for key terms
- **Headers** to break up sections
- **Code blocks** for technical details
- **Visual diagrams** where helpful

#### Avoid:
- Long walls of text
- Complex sentences
- Jargon without explanation
- Multiple concepts in one paragraph

---

### 6. **Include Actionable Checklists**

For operational workflows, provide:

#### Pre-Flight Checklist
- [ ] Prerequisites met
- [ ] Permissions verified
- [ ] Maintenance window scheduled
- [ ] Backup completed

#### Post-Execution Validation
- [ ] Service status verified
- [ ] Traffic flowing correctly
- [ ] No alarms present
- [ ] Documentation updated

---

### 7. **Document Impact Timeline**

For workflows that affect live systems, show **when** impact occurs:

```markdown
| Step | Action | Traffic Impact | Duration |
|------|--------|----------------|----------|
| 1-2  | Planning | ✅ None | 5 min |
| 3    | **Reconfigure devices** | ⚠️ **Outage** | 30 sec |
| 4-5  | Validation | ✅ Minimal | 2 min |
```

This lets operators quickly assess risk and plan accordingly.

---

### 8. **Separate "What" from "How" from "Why"**

Don't mix these in the same section:

#### What (Reference)
- "This workflow changes optical frequencies"
- Facts only, no explanation

#### How (How-To Guide)
- "Step 1: Open the workflow"
- "Step 2: Enter new frequency"
- Procedural only

#### Why (Explanation)
- "Frequencies must align with ITU-T grid because..."
- "This prevents interference because..."
- Context and rationale

---

### 9. **Use Consistent Formatting**

Establish patterns and stick to them:

#### Function Documentation:
```markdown
### Function Name
**Purpose**: [One line]
**Input**: [Parameters]
**Output**: [What it returns]
**Network Impact**: [Traffic/system changes]
**Example**:
```python
example_code()
```
```

#### Workflow Steps:
```markdown
### Step X: [Action Verb] [Object]
**Function**: `function_name()`
**What it does**: [Brief description]
**Network Impact**: [None/Minimal/Critical]
**Duration**: [Time estimate]
```

---

### 10. **Make it Maintainable**

Good documentation should be **easy to update**:

#### Version Control
- Keep documentation in source code (as docstrings)
- Use version control (git)
- Tag documentation with code versions

#### Single Source of Truth
- Avoid duplicating information
- Use references and links
- Generate documentation from code where possible

#### Review Process
- Update documentation with code changes
- Review docs in pull requests
- Test documentation with new users

---

## Specific Guidelines for Network Automation Workflows

### 1. **Network Impact Must Be Front and Center**

Network engineers need to know immediately:
- Will traffic drop?
- When and for how long?
- Which services/circuits are affected?

### 2. **Include Pre-Change and Post-Change Validation**

Every workflow should document:
- **Pre-change checks**: What to verify before starting
- **Expected results**: What success looks like
- **Post-change validation**: How to confirm it worked
- **Rollback procedure**: How to undo if needed

### 3. **Document Device-Specific Behavior**

If workflows interact with different platforms:
- Clearly separate platform-specific sections
- Show what's different between platforms
- Don't bury platform variations in prose

### 4. **Show Command Examples**

For CLI-based operations:
- Include actual command examples
- Show expected output
- Document error conditions

---

## Anti-Patterns to Avoid

### ❌ **Don't:**

1. **Mix documentation types**
   - Don't put tutorials in reference docs
   - Don't put explanations in how-to guides

2. **Bury critical information**
   - Don't hide traffic impact in a footnote
   - Don't make users read 10 paragraphs to find prerequisites

3. **Use vague language**
   - ❌ "This may cause some disruption"
   - ✅ "This will cause a 30-second traffic outage"

4. **Assume knowledge**
   - ❌ "Configure the OSNC as usual"
   - ✅ "Create OSNC with passbandlist=[start, end] and carrierlist=[freq, bw]"

5. **Write for yourself**
   - ❌ Document what YOU know
   - ✅ Document what USERS need to know

6. **Make it too detailed upfront**
   - ❌ Explain every parameter in the introduction
   - ✅ Progressive disclosure: summary → details → deep-dive

---

## Template for Workflow Documentation

```markdown
"""Workflow Name

## Quick Summary

**What it does**: [One sentence]

**Traffic Impact**: [None/Brief outage/Extended downtime]

**Use when**: [Scenario]

**Cannot do**: [Limitations]

---

## Impact Timeline

| Step | Action | Traffic Impact | Duration |
|------|--------|----------------|----------|
| 1-2  | Input/validation | ✅ None | 2 min |
| 3    | **Device config** | ⚠️ **Outage** | 30 sec |
| 4    | Verification | ✅ None | 1 min |

**Total time**: X minutes

---

## Before You Run

### Prerequisites
- [ ] Requirement 1
- [ ] Requirement 2

### Constraints
- Cannot do X
- Must have Y

### Rollback
[How to undo this operation]

---

## After Running

### Validation
1. Check X
2. Verify Y

### If Something Goes Wrong
- Error type 1 → Solution
- Error type 2 → Solution

---

## Procedure

### Step 1: [Action]
**Function**: `function_name()`
**What it does**: [Description]
**Network Impact**: [Details]

[Detailed explanation of what happens]

[Repeat for each step]

---

<details>
<summary>Technical Reference</summary>

## Platform Details
[Deep technical information]

## Parameters
[Detailed specifications]

## Related Workflows
[Links to related documentation]

</details>
"""
```

---

## Tools and Techniques

### Documentation Generation
- **MkDocs + mkdocstrings**: Generate docs from Python docstrings
- **Sphinx**: Comprehensive documentation builder
- **Swagger/OpenAPI**: API documentation

### Diagramming
- **Mermaid**: Flowcharts in markdown
- **PlantUML**: UML diagrams
- **Draw.io**: Visual diagrams

### Validation
- **markdownlint**: Check markdown formatting
- **Vale**: Prose linting
- **Grammarly**: Grammar checking

---

## Summary: The Documentation Hierarchy

```
LEVEL 1: Can I use this? (10 seconds)
  → Quick summary: what, impact, use-case

LEVEL 2: What do I need to know? (2 minutes)
  → Prerequisites, constraints, timeline

LEVEL 3: How do I run it? (10 minutes)
  → Step-by-step procedure

LEVEL 4: How does it work? (30+ minutes)
  → Technical deep-dive, platform details
```

**Remember**: Most users stop at Level 1 or 2. Make those levels excellent.

---

## References

- Diátaxis Framework: https://diataxis.fr/
- Divio Documentation System: https://docs.divio.com/documentation-system/
- Read the Docs: Documentation structure guide
- Atlassian: Software documentation best practices
