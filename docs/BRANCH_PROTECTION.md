# حماية فرع `main`

أدوات التكامل الحالية لا تستطيع تفعيل Branch Protection عبر API من هذه الجلسة.
فعّلها يدوياً (دقيقتان) — هذا مطلوب لفرض نجاح CI قبل الدمج.

## الخطوات (GitHub UI)

1. افتح: https://github.com/Johanne012/zyntra-platform/settings/branches
2. **Add branch protection rule** (أو Ruleset).
3. Branch name pattern: `main`
4. فعّل:
   - **Require a pull request before merging**
   - **Require status checks to pass before merging**
     - اختر فحوصات CI: `Gateway` · `Agents` · `Web structure`
   - **Require conversation resolution before merging** (مستحسن)
   - **Do not allow bypassing the above settings** (إن ظهر)
   - **Restrict who can push to matching branches** → أنت فقط
5. احفظ.

## بديل Rulesets (أحدث)

Settings → Rules → Rulesets → New branch ruleset:

- Target: `main`
- Restrict deletions
- Require pull request
- Required status checks: أسماء jobs من `.github/workflows/ci.yml`

## بعد التفعيل

- لا دفع مباشر إلى `main` (إلا إن سمحت لنفسك صراحة).
- كل تغيير عبر PR + CI أخضر.

## تحقق سريع

```bash
# يجب أن يُرفض إن كانت الحماية مفعّلة بدون صلاحية bypass
git push origin main
```
