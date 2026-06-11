---
name: coding-standards
description: Universal coding standards, best practices, and patterns for TypeScript, JavaScript, React, and Node.js development.
priority: highest
auto_trigger: true
model: haiku
---

# Coding Standards & Best Practices

Universal coding standards applicable across all projects.

**IMPORTANT**: This skill is ALWAYS ACTIVE. Security checks take HIGHEST PRIORITY and Claude MUST alert the user to any security issues found in code.

---

## SECURITY FIRST (HIGHEST PRIORITY)

**Claude MUST check for and alert on these issues before any code is written or modified:**

### Critical Security Checks

#### 1. Injection Attacks (SQL, NoSQL, Command, XSS)

```typescript
// ❌ CRITICAL VULNERABILITY: SQL Injection
const query = `SELECT * FROM users WHERE id = ${userId}`  // NEVER DO THIS
await db.query(`DELETE FROM orders WHERE id = '${orderId}'`)  // VULNERABLE

// ✅ SAFE: Parameterized queries
const query = 'SELECT * FROM users WHERE id = @userId'
await db.query('DELETE FROM orders WHERE id = @orderId', { orderId })

// ❌ CRITICAL VULNERABILITY: XSS
element.innerHTML = userInput  // NEVER DO THIS
dangerouslySetInnerHTML={{ __html: userContent }}  // AUDIT REQUIRED

// ✅ SAFE: Text content or sanitization
element.textContent = userInput
import DOMPurify from 'dompurify'
dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }}

// ❌ CRITICAL VULNERABILITY: Command Injection
exec(`ls ${userInput}`)  // NEVER DO THIS
spawn('bash', ['-c', userCommand])  // VULNERABLE

// ✅ SAFE: Whitelist commands, escape inputs
import { execFile } from 'child_process'
execFile('ls', ['-la', sanitizedPath])  // Use execFile with array args
```

#### 2. Authentication & Authorization

```typescript
// ❌ VULNERABILITY: Broken authentication
if (password === storedPassword) { }  // Plain text comparison
jwt.verify(token, 'hardcoded-secret')  // Hardcoded secret
localStorage.setItem('authToken', token)  // XSS vulnerable storage

// ✅ SAFE: Proper auth handling
import bcrypt from 'bcrypt'
const isValid = await bcrypt.compare(password, hashedPassword)
jwt.verify(token, process.env.JWT_SECRET!)  // Environment variable
// Use httpOnly cookies for tokens

// ❌ VULNERABILITY: Missing authorization
app.get('/admin/users', (req, res) => {  // No auth check!
  return getAllUsers()
})

// ✅ SAFE: Always verify authorization
app.get('/admin/users', requireAuth, requireRole('admin'), (req, res) => {
  return getAllUsers()
})
```

#### 3. Sensitive Data Exposure

```typescript
// ❌ CRITICAL: Exposing secrets
console.log('API Key:', apiKey)  // NEVER log secrets
const config = { apiKey: 'sk-123456789' }  // Hardcoded secrets
error.stack  // May expose internal paths

// ✅ SAFE: Protect sensitive data
console.log('API Key:', '[REDACTED]')
const config = { apiKey: process.env.API_KEY }
// Use structured logging that filters sensitive fields

// ❌ VULNERABILITY: Returning sensitive data
return { user: { ...user } }  // May include password hash

// ✅ SAFE: Explicit field selection
return {
  user: {
    id: user.id,
    name: user.name,
    email: user.email
    // Explicitly omit password, tokens, etc.
  }
}
```

#### 4. CSRF & CORS

```typescript
// ❌ VULNERABILITY: Overly permissive CORS
app.use(cors({ origin: '*' }))  // Allows any origin

// ✅ SAFE: Restrict origins
app.use(cors({
  origin: ['https://yourdomain.com'],
  credentials: true
}))

// ❌ VULNERABILITY: No CSRF protection on state-changing routes
app.post('/api/transfer', (req, res) => { })  // No CSRF token

// ✅ SAFE: CSRF tokens for state changes
// Use SameSite cookies + CSRF tokens for forms
```

#### 5. Input Validation (ALWAYS VALIDATE)

```typescript
// ❌ VULNERABILITY: Trusting client input
const { amount } = req.body
await transferMoney(userId, amount)  // No validation!

// ✅ SAFE: Always validate and sanitize
import { z } from 'zod'

const TransferSchema = z.object({
  amount: z.number().positive().max(10000),
  toAccount: z.string().uuid()
})

const validated = TransferSchema.parse(req.body)
await transferMoney(userId, validated.amount, validated.toAccount)
```

#### 6. .NET/C# Specific Security

```csharp
// ❌ VULNERABILITY: SQL Injection in EF/ADO.NET
var query = $"SELECT * FROM Users WHERE Name = '{name}'"  // NEVER
context.Users.FromSqlRaw($"SELECT * FROM Users WHERE Id = {id}")  // VULNERABLE

// ✅ SAFE: Parameterized queries
context.Users.FromSqlInterpolated($"SELECT * FROM Users WHERE Id = {id}")
context.Users.Where(u => u.Id == id)  // LINQ is safe

// ❌ VULNERABILITY: Path traversal
var path = Path.Combine(uploadDir, userFilename)  // Can escape directory

// ✅ SAFE: Validate paths
var safeName = Path.GetFileName(userFilename)  // Strip path components
var fullPath = Path.GetFullPath(Path.Combine(uploadDir, safeName))
if (!fullPath.StartsWith(uploadDir)) throw new SecurityException()

// ❌ VULNERABILITY: Insecure deserialization
JsonConvert.DeserializeObject<T>(json, new JsonSerializerSettings {
  TypeNameHandling = TypeNameHandling.All  // DANGEROUS
})

// ✅ SAFE: Restrict deserialization
JsonConvert.DeserializeObject<T>(json)  // Default settings
```

### Security Alerts Format

When Claude detects a security issue, it MUST alert in this format:

```
⚠️ SECURITY ALERT: [Vulnerability Type]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Location: [file:line]
Severity: CRITICAL | HIGH | MEDIUM | LOW
Issue: [Brief description]
Risk: [What could happen if exploited]
Fix: [How to fix it]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Security Checklist (Run Before Every Code Change)

- [ ] No hardcoded secrets, API keys, or passwords
- [ ] All user input validated and sanitized
- [ ] SQL queries use parameterized statements
- [ ] No innerHTML with user content (or properly sanitized)
- [ ] Authentication required on protected routes
- [ ] Authorization checked before data access
- [ ] Sensitive data not logged or exposed in responses
- [ ] CORS restricted to allowed origins
- [ ] File uploads validated (type, size, name)
- [ ] Error messages don't expose internal details

---

## Code Quality Principles

### 1. Readability First
- Code is read more than written
- Clear variable and function names
- Self-documenting code preferred over comments
- Consistent formatting

### 2. KISS (Keep It Simple, Stupid)
- Simplest solution that works
- Avoid over-engineering
- No premature optimization
- Easy to understand > clever code

### 3. DRY (Don't Repeat Yourself)
- Extract common logic into functions
- Create reusable components
- Share utilities across modules
- Avoid copy-paste programming

### 4. YAGNI (You Aren't Gonna Need It)
- Don't build features before they're needed
- Avoid speculative generality
- Add complexity only when required
- Start simple, refactor when needed

## TypeScript/JavaScript Standards

### Variable Naming

```typescript
// ✅ GOOD: Descriptive names
const marketSearchQuery = 'election'
const isUserAuthenticated = true
const totalRevenue = 1000

// ❌ BAD: Unclear names
const q = 'election'
const flag = true
const x = 1000
```

### Function Naming

```typescript
// ✅ GOOD: Verb-noun pattern
async function fetchMarketData(marketId: string) { }
function calculateSimilarity(a: number[], b: number[]) { }
function isValidEmail(email: string): boolean { }

// ❌ BAD: Unclear or noun-only
async function market(id: string) { }
function similarity(a, b) { }
function email(e) { }
```

### Immutability Pattern (CRITICAL)

```typescript
// ✅ ALWAYS use spread operator
const updatedUser = {
  ...user,
  name: 'New Name'
}

const updatedArray = [...items, newItem]

// ❌ NEVER mutate directly
user.name = 'New Name'  // BAD
items.push(newItem)     // BAD
```

### Error Handling

```typescript
// ✅ GOOD: Comprehensive error handling
async function fetchData(url: string) {
  try {
    const response = await fetch(url)

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Fetch failed:', error)
    throw new Error('Failed to fetch data')
  }
}

// ❌ BAD: No error handling
async function fetchData(url) {
  const response = await fetch(url)
  return response.json()
}
```

### Async/Await Best Practices

```typescript
// ✅ GOOD: Parallel execution when possible
const [users, markets, stats] = await Promise.all([
  fetchUsers(),
  fetchMarkets(),
  fetchStats()
])

// ❌ BAD: Sequential when unnecessary
const users = await fetchUsers()
const markets = await fetchMarkets()
const stats = await fetchStats()
```

### Type Safety

```typescript
// ✅ GOOD: Proper types
interface Market {
  id: string
  name: string
  status: 'active' | 'resolved' | 'closed'
  created_at: Date
}

function getMarket(id: string): Promise<Market> {
  // Implementation
}

// ❌ BAD: Using 'any'
function getMarket(id: any): Promise<any> {
  // Implementation
}
```

## React Best Practices

### Component Structure

```typescript
// ✅ GOOD: Functional component with types
interface ButtonProps {
  children: React.ReactNode
  onClick: () => void
  disabled?: boolean
  variant?: 'primary' | 'secondary'
}

export function Button({
  children,
  onClick,
  disabled = false,
  variant = 'primary'
}: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
    >
      {children}
    </button>
  )
}

// ❌ BAD: No types, unclear structure
export function Button(props) {
  return <button onClick={props.onClick}>{props.children}</button>
}
```

### Custom Hooks

```typescript
// ✅ GOOD: Reusable custom hook
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => clearTimeout(handler)
  }, [value, delay])

  return debouncedValue
}

// Usage
const debouncedQuery = useDebounce(searchQuery, 500)
```

### State Management

```typescript
// ✅ GOOD: Proper state updates
const [count, setCount] = useState(0)

// Functional update for state based on previous state
setCount(prev => prev + 1)

// ❌ BAD: Direct state reference
setCount(count + 1)  // Can be stale in async scenarios
```

### Conditional Rendering

```typescript
// ✅ GOOD: Clear conditional rendering
{isLoading && <Spinner />}
{error && <ErrorMessage error={error} />}
{data && <DataDisplay data={data} />}

// ❌ BAD: Ternary hell
{isLoading ? <Spinner /> : error ? <ErrorMessage error={error} /> : data ? <DataDisplay data={data} /> : null}
```

## API Design Standards

### REST API Conventions

```
GET    /api/markets              # List all markets
GET    /api/markets/:id          # Get specific market
POST   /api/markets              # Create new market
PUT    /api/markets/:id          # Update market (full)
PATCH  /api/markets/:id          # Update market (partial)
DELETE /api/markets/:id          # Delete market

# Query parameters for filtering
GET /api/markets?status=active&limit=10&offset=0
```

### Response Format

```typescript
// ✅ GOOD: Consistent response structure
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  meta?: {
    total: number
    page: number
    limit: number
  }
}

// Success response
return NextResponse.json({
  success: true,
  data: markets,
  meta: { total: 100, page: 1, limit: 10 }
})

// Error response
return NextResponse.json({
  success: false,
  error: 'Invalid request'
}, { status: 400 })
```

### Input Validation

```typescript
import { z } from 'zod'

// ✅ GOOD: Schema validation
const CreateMarketSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().min(1).max(2000),
  endDate: z.string().datetime(),
  categories: z.array(z.string()).min(1)
})

export async function POST(request: Request) {
  const body = await request.json()

  try {
    const validated = CreateMarketSchema.parse(body)
    // Proceed with validated data
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      }, { status: 400 })
    }
  }
}
```

## File Organization

### Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   ├── markets/           # Market pages
│   └── (auth)/           # Auth pages (route groups)
├── components/            # React components
│   ├── ui/               # Generic UI components
│   ├── forms/            # Form components
│   └── layouts/          # Layout components
├── hooks/                # Custom React hooks
├── lib/                  # Utilities and configs
│   ├── api/             # API clients
│   ├── utils/           # Helper functions
│   └── constants/       # Constants
├── types/                # TypeScript types
└── styles/              # Global styles
```

### File Naming

```
components/Button.tsx          # PascalCase for components
hooks/useAuth.ts              # camelCase with 'use' prefix
lib/formatDate.ts             # camelCase for utilities
types/market.types.ts         # camelCase with .types suffix
```

## Comments & Documentation

### When to Comment

```typescript
// ✅ GOOD: Explain WHY, not WHAT
// Use exponential backoff to avoid overwhelming the API during outages
const delay = Math.min(1000 * Math.pow(2, retryCount), 30000)

// Deliberately using mutation here for performance with large arrays
items.push(newItem)

// ❌ BAD: Stating the obvious
// Increment counter by 1
count++

// Set name to user's name
name = user.name
```

### JSDoc for Public APIs

```typescript
/**
 * Searches markets using semantic similarity.
 *
 * @param query - Natural language search query
 * @param limit - Maximum number of results (default: 10)
 * @returns Array of markets sorted by similarity score
 * @throws {Error} If OpenAI API fails or Redis unavailable
 *
 * @example
 * ```typescript
 * const results = await searchMarkets('election', 5)
 * console.log(results[0].name) // "Trump vs Biden"
 * ```
 */
export async function searchMarkets(
  query: string,
  limit: number = 10
): Promise<Market[]> {
  // Implementation
}
```

## Performance Best Practices

### Memoization

```typescript
import { useMemo, useCallback } from 'react'

// ✅ GOOD: Memoize expensive computations
const sortedMarkets = useMemo(() => {
  return markets.sort((a, b) => b.volume - a.volume)
}, [markets])

// ✅ GOOD: Memoize callbacks
const handleSearch = useCallback((query: string) => {
  setSearchQuery(query)
}, [])
```

### Lazy Loading

```typescript
import { lazy, Suspense } from 'react'

// ✅ GOOD: Lazy load heavy components
const HeavyChart = lazy(() => import('./HeavyChart'))

export function Dashboard() {
  return (
    <Suspense fallback={<Spinner />}>
      <HeavyChart />
    </Suspense>
  )
}
```

### Database Queries

```typescript
// ✅ GOOD: Select only needed columns
const { data } = await supabase
  .from('markets')
  .select('id, name, status')
  .limit(10)

// ❌ BAD: Select everything
const { data } = await supabase
  .from('markets')
  .select('*')
```

## Testing Standards

### Test Structure (AAA Pattern)

```typescript
test('calculates similarity correctly', () => {
  // Arrange
  const vector1 = [1, 0, 0]
  const vector2 = [0, 1, 0]

  // Act
  const similarity = calculateCosineSimilarity(vector1, vector2)

  // Assert
  expect(similarity).toBe(0)
})
```

### Test Naming

```typescript
// ✅ GOOD: Descriptive test names
test('returns empty array when no markets match query', () => { })
test('throws error when OpenAI API key is missing', () => { })
test('falls back to substring search when Redis unavailable', () => { })

// ❌ BAD: Vague test names
test('works', () => { })
test('test search', () => { })
```

## Code Smell Detection

Watch for these anti-patterns:

### 1. Long Functions
```typescript
// ❌ BAD: Function > 50 lines
function processMarketData() {
  // 100 lines of code
}

// ✅ GOOD: Split into smaller functions
function processMarketData() {
  const validated = validateData()
  const transformed = transformData(validated)
  return saveData(transformed)
}
```

### 2. Deep Nesting
```typescript
// ❌ BAD: 5+ levels of nesting
if (user) {
  if (user.isAdmin) {
    if (market) {
      if (market.isActive) {
        if (hasPermission) {
          // Do something
        }
      }
    }
  }
}

// ✅ GOOD: Early returns
if (!user) return
if (!user.isAdmin) return
if (!market) return
if (!market.isActive) return
if (!hasPermission) return

// Do something
```

### 3. Magic Numbers
```typescript
// ❌ BAD: Unexplained numbers
if (retryCount > 3) { }
setTimeout(callback, 500)

// ✅ GOOD: Named constants
const MAX_RETRIES = 3
const DEBOUNCE_DELAY_MS = 500

if (retryCount > MAX_RETRIES) { }
setTimeout(callback, DEBOUNCE_DELAY_MS)
```

**Remember**: Code quality is not negotiable. Clear, maintainable code enables rapid development and confident refactoring.

---

## React + .NET Security Patterns

### Frontend (React/TypeScript)

#### API Calls - Always Validate Responses

```typescript
// ✅ SAFE: Validate API responses
import { z } from 'zod'

const UserSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().email()
})

async function fetchUser(id: number) {
  const response = await api.get(`/users/${id}`)
  return UserSchema.parse(response.data)  // Validates response
}
```

#### Form Handling - Validate Before Submit

```typescript
// ✅ SAFE: Validate form data
const formSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Password must be 8+ characters'),
  amount: z.number().positive().max(10000)
})

const handleSubmit = (data: FormData) => {
  const result = formSchema.safeParse(data)
  if (!result.success) {
    setErrors(result.error.flatten())
    return
  }
  // Proceed with validated data
}
```

#### Never Trust URL Parameters

```typescript
// ❌ VULNERABLE: Direct use of params
const { id } = useParams()
await deleteItem(id)  // id could be manipulated

// ✅ SAFE: Validate and authorize
const { id } = useParams()
const numericId = z.coerce.number().positive().parse(id)
// Backend still verifies user owns this resource
```

### Backend (.NET/C#)

#### Controller Security

```csharp
// ✅ SAFE: Authorize + validate + audit
[Authorize]
[HttpDelete("{id}")]
public async Task<IActionResult> DeleteJob(int id)
{
    var userId = User.GetUserId();  // From JWT claims

    // Verify ownership
    var job = await _context.Jobs.FindAsync(id);
    if (job == null) return NotFound();
    if (job.OwnerId != userId) return Forbid();  // Authorization check

    _logger.LogInformation("User {UserId} deleting job {JobId}", userId, id);

    _context.Jobs.Remove(job);
    await _context.SaveChangesAsync();

    return NoContent();
}
```

#### DTO Pattern - Never Expose Entities

```csharp
// ❌ VULNERABLE: Exposing entity directly
[HttpGet("{id}")]
public async Task<User> GetUser(int id)
{
    return await _context.Users.FindAsync(id);  // Exposes password hash!
}

// ✅ SAFE: Use DTOs
[HttpGet("{id}")]
public async Task<UserDto> GetUser(int id)
{
    var user = await _context.Users.FindAsync(id);
    return new UserDto
    {
        Id = user.Id,
        Name = user.Name,
        Email = user.Email
        // Password, tokens, etc. NOT included
    };
}
```

#### File Upload Security

```csharp
// ✅ SAFE: Validate file uploads
[HttpPost("upload")]
public async Task<IActionResult> Upload(IFormFile file)
{
    // Check file size
    if (file.Length > 5 * 1024 * 1024)  // 5MB max
        return BadRequest("File too large");

    // Check content type (don't trust extension)
    var allowedTypes = new[] { "image/jpeg", "image/png", "application/pdf" };
    if (!allowedTypes.Contains(file.ContentType))
        return BadRequest("Invalid file type");

    // Generate safe filename
    var safeFileName = $"{Guid.NewGuid()}{Path.GetExtension(file.FileName)}";
    var filePath = Path.Combine(_uploadPath, safeFileName);

    // Verify path doesn't escape upload directory
    if (!Path.GetFullPath(filePath).StartsWith(_uploadPath))
        return BadRequest("Invalid path");

    using var stream = new FileStream(filePath, FileMode.Create);
    await file.CopyToAsync(stream);

    return Ok(new { fileName = safeFileName });
}
```

---

## Claude's Security Behavior

### When Reading Code
Claude will automatically scan for:
1. Hardcoded credentials or API keys
2. SQL injection vulnerabilities
3. XSS vulnerabilities (innerHTML, dangerouslySetInnerHTML)
4. Missing input validation
5. Insecure authentication patterns
6. Authorization bypass risks
7. Sensitive data exposure

### When Writing Code
Claude will:
1. Always use parameterized queries
2. Always validate input with Zod or equivalent
3. Never hardcode secrets
4. Always use proper auth/authz patterns
5. Never expose sensitive data in responses
6. Use secure defaults for CORS, cookies, etc.

### When Issues Are Found
Claude MUST:
1. Stop and alert the user immediately
2. Explain the vulnerability and its risk
3. Provide the secure alternative
4. Not proceed until the user acknowledges

### Alert Examples

```
⚠️ SECURITY ALERT: SQL Injection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Location: UserService.cs:45
Severity: CRITICAL
Issue: String interpolation in SQL query
Risk: Attackers can execute arbitrary SQL, steal/delete data
Fix: Use parameterized query or LINQ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ SECURITY ALERT: XSS Vulnerability
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Location: CommentDisplay.tsx:23
Severity: HIGH
Issue: User content rendered with dangerouslySetInnerHTML
Risk: Attackers can inject malicious scripts
Fix: Use DOMPurify to sanitize or render as text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ SECURITY ALERT: Hardcoded Secret
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Location: config.ts:12
Severity: CRITICAL
Issue: API key hardcoded in source code
Risk: Secret exposed in version control
Fix: Use environment variable (process.env.API_KEY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

**SECURITY IS NOT OPTIONAL. Claude will always prioritize security over convenience.**
