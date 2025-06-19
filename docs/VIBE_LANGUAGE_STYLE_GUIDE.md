# 🎵 Vibe Language Style Guide

A comprehensive guide for maintaining consistent, engaging, and professional vibe language throughout the vibe-check-mcp tool.

## 🎯 Purpose

This style guide ensures that vibe-check-mcp maintains its unique personality - friendly and approachable while remaining professional and helpful. The tool is designed "for vibe coders" and should feel like it was built by developers who genuinely care about code quality and team dynamics.

## 🎨 Core Principles

### 1. **Helpful First**
Every message should be actionable and clear, regardless of vibe level. Personality never sacrifices clarity or usefulness.

### 2. **Context Aware**
- **Enterprise/Professional contexts**: Restrained, focused on value
- **Development/Casual contexts**: Balanced personality and professionalism  
- **Personal/Informal contexts**: Full vibe expression

### 3. **Inclusive and Universal**
- Use universal references and metaphors
- Avoid cultural-specific slang or exclusionary language
- Keep emojis professional and meaningful

### 4. **Technically Accurate**
Vibe language enhances but never replaces technical precision. Error messages must still be debuggable.

## 🎛️ Vibe Levels System

The vibe-check-mcp tool supports three configurable vibe levels via the `VIBE_LEVEL` environment variable:

### **Professional** (`VIBE_LEVEL=professional`)
**Use case**: Enterprise environments, formal documentation, regulatory contexts

**Characteristics**:
- Minimal personality, maximum clarity
- Professional emojis (✅❌⚠️💡)
- Technical terminology
- Formal error messages

**Examples**:
```
✅ Analysis complete
❌ Error: Configuration not found
⚠️ High priority issue detected
💡 Recommendation: Use standard APIs
```

### **Casual** (`VIBE_LEVEL=casual`) *[Default]*
**Use case**: General development, team collaboration, most use cases

**Characteristics**:
- Balanced personality and professionalism
- Conversational but clear language
- Helpful emojis with purpose
- Friendly error handling

**Examples**:
```
✅ Vibe check complete
😅 Oops: Config vibes aren't right
⚠️ Major vibe disruption detected
💫 Need GitHub integration for full vibe powers
```

### **Playful** (`VIBE_LEVEL=playful`)
**Use case**: Personal projects, creative environments, relaxed teams

**Characteristics**:
- Full personality expression
- Creative and engaging language
- Expressive emojis and metaphors
- Maximum approachability

**Examples**:
```
✨ Vibe check complete - you're killing it!
🚨 Whoopsie: Config vibes are totally off
⚠️ Vibe killer on the loose!
🪄 Need GitHub magic for maximum vibe powers
```

## 📝 Message Type Guidelines

### Success Messages

| Context | Professional | Casual | Playful |
|---------|-------------|--------|---------|
| Analysis complete | "Analysis complete" | "Vibe check complete" | "Vibe check complete - you're killing it!" |
| No issues found | "No concerning patterns detected" | "Clean vibes detected! 🎯" | "Squeaky clean vibes! No drama here! 🌟" |
| Task finished | "Task completed successfully" | "All done - looking good!" | "Nailed it! 🎉" |

### Error Messages

| Context | Professional | Casual | Playful |
|---------|-------------|--------|---------|
| Error prefix | "❌ Error:" | "😅 Oops:" | "🚨 Whoopsie:" |
| Failed action | "Failed to" | "Couldn't" | "Epic fail on" |
| Config issues | "Configuration error" | "Config vibes aren't right" | "Config vibes are totally off" |
| File not found | "File not found" | "Can't find that file" | "That file is playing hide and seek 📁" |
| API timeout | "Request timeout" | "Request took too long ⏰" | "The vibes took forever to respond ⏰" |

### Status Messages

| Context | Professional | Casual | Playful |
|---------|-------------|--------|---------|
| Starting work | "Starting analysis" | "Checking the vibes..." | "Time to check those vibes! 🔍" |
| Processing | "Processing file" | "Scanning for vibe disruptions" | "Hunting for vibe killers" |
| Pattern found | "Pattern detected" | "Vibe pattern spotted" | "Caught a vibe killer!" |

### Educational/Coaching Messages

| Context | Professional | Casual | Playful |
|---------|-------------|--------|---------|
| Recommendation | "Recommendation:" | "Vibe restoration:" | "Let's restore those good vibes:" |
| Severity high | "🚨 HIGH PRIORITY" | "🚨 Major vibe disruption" | "🚨 MASSIVE vibe killer alert!" |
| Learn more | "Review documentation" | "Dig into the learning stuff" | "Time for some vibe education!" |

## 🛠️ Implementation Patterns

### **Replace Formal Patterns**

❌ **Avoid**: Technical, cold language
```
"Error: Analysis failed"
"Invalid configuration detected" 
"Process completed successfully"
"Critical issues identified"
```

✅ **Use**: Vibe-appropriate alternatives
```
"😅 Oops: Vibe check hit a snag"
"Config vibes aren't right"
"Analysis done - looking good!"
"Major vibe killers spotted 🚨"
```

### **Emoji Guidelines**

**Always Use Purpose-Driven Emojis**:
- ✅ Success, completion, positive outcomes
- ❌ Errors, failures, blocking issues  
- ⚠️ Warnings, concerns, caution needed
- 💡 Suggestions, tips, recommendations
- 🔍 Analysis, searching, investigating
- 📖 Learning, documentation, education
- 🎯 Precision, accuracy, targeting
- ✨ Enhancement, improvement, polish

**Vibe Level Specific Emojis**:
- **Professional**: Stick to functional emojis (✅❌⚠️💡)
- **Casual**: Add personality emojis (😅🎯💫⏰)
- **Playful**: Full expression (🚨🪄🌟🎉👀)

### **Language Patterns**

**Use Contractions** (Casual/Playful):
- "can't" instead of "cannot"
- "couldn't" instead of "could not"
- "doesn't" instead of "does not"

**Use Active Voice**:
- "Vibe check found issues" vs "Issues were found"
- "GitHub's giving us attitude" vs "GitHub API returned error"

**Use Conversational Transitions**:
- "Let's" instead of "We should"
- "Time to" instead of "It is necessary to"
- "How about" instead of "Consider"

## 🎯 Context-Specific Guidelines

### **GitHub Integration Messages**
Replace technical API language with conversational explanations:
```
❌ "HTTP 404: Resource not found"
✅ "Can't find that file - vibes are off 📁"

❌ "Authentication failed"  
✅ "GitHub's not recognizing us - need those auth vibes"

❌ "Rate limit exceeded"
✅ "GitHub wants us to slow down - taking a breather ⏰"
```

### **Pattern Detection Messages**
Make anti-pattern explanations feel like friendly coaching:
```
❌ "Infrastructure-Without-Implementation pattern detected"
✅ "Vibe killer spotted: building infrastructure before testing basics"

❌ "High severity anti-pattern"
✅ "Major vibe disruption - this could cause real headaches"

❌ "Immediate remediation required"
✅ "Let's fix this vibe before it spreads"
```

### **Educational Content**
Transform academic explanations into relatable guidance:
```
❌ "This pattern leads to technical debt accumulation"
✅ "This pattern creates more work later - nobody wants that!"

❌ "Insufficient validation of external dependencies"
✅ "Didn't check if the tools actually work - classic vibe killer"

❌ "Premature optimization detected"
✅ "Building fancy stuff before proving it works - we've all been there"
```

## 🧪 Testing Your Vibe Language

### **Questions to Ask**:

1. **Would a developer friend say this?** - Natural, conversational tone
2. **Is it still helpful?** - Actionable information preserved
3. **Does it match the vibe level?** - Appropriate for context
4. **Is it inclusive?** - Welcomes all developers
5. **Can you debug with it?** - Technical precision maintained

### **Red Flags**:
- ❌ Too academic or formal
- ❌ Sacrifices clarity for personality
- ❌ Uses exclusionary slang
- ❌ Loses technical accuracy
- ❌ Feels forced or artificial

## 📚 Examples in Context

### **CLI Command Help**
```bash
# Professional
claude analyze-issue 42 --comprehensive

# Casual  
vibe check issue 42

# Playful
deep vibe check issue 42 - let's see what's up!
```

### **Error Recovery**
```
Professional: "GitHub API authentication required. Configure token."
Casual: "Need GitHub token for full vibe powers 💫"
Playful: "GitHub wants to know who we are - time for some auth magic! 🪄"
```

### **Success Celebration**
```
Professional: "Analysis completed. No issues detected."
Casual: "Vibe check complete - looking good! ✨"
Playful: "Vibe check done and dusted! Your code is absolutely vibing! 🎉"
```

## 🚀 Implementation Checklist

When adding new messages:

- [ ] **Choose appropriate vibe level** for context
- [ ] **Use vibe config system** (`get_vibe_config()`, `vibe_message()`)
- [ ] **Test across all three levels** 
- [ ] **Preserve technical accuracy**
- [ ] **Include helpful actions** when appropriate
- [ ] **Use purpose-driven emojis**
- [ ] **Keep it conversational** but professional
- [ ] **Ensure accessibility** and clarity

## 🎯 Success Metrics

**Good vibe language achieves**:
- ✅ Developers feel welcomed and supported
- ✅ Technical information remains clear and actionable
- ✅ Professional contexts feel appropriate
- ✅ Error messages help rather than frustrate
- ✅ Educational content feels approachable
- ✅ Tool personality is consistent and authentic

**The vibe-check-mcp tool should feel like a knowledgeable friend who genuinely wants to help you write better code and avoid costly mistakes.**

---

*This style guide evolves with the tool. When in doubt, prioritize helpfulness over personality, and remember: we're here to catch anti-patterns before they become expensive problems, with just the right amount of vibe.* ✨