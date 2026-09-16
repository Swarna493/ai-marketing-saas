import { useState, useEffect } from 'react'
import './App.css'

const API_BASE = 'http://127.0.0.1:5000'

function App() {
  const [activeTab, setActiveTab] = useState('caption')
  const tabs = [
        { id: 'adcopy', label: 'Ad Copy' },
    { id: 'productdesc', label: 'Product Desc' },
    { id: 'slogan', label: 'Slogan' },
    { id: 'caption', label: 'Caption' },
    { id: 'hashtag', label: 'Hashtags' },
    { id: 'seo', label: 'SEO Writer' },
    { id: 'email', label: 'Email' },
    { id: 'competitor', label: 'Competitor' },
    { id: 'image', label: 'Image' },
    { id: 'landing', label: 'Landing Page' },
    { id: 'scheduler', label: 'Scheduler' },
    { id: 'analytics', label: 'Analytics' },
    { id: 'history', label: 'History' },
  ]
  return (
    <div className="app-wrapper">
      <nav className="navbar">
        <h2 className="logo">✨ MarketMate AI</h2>
        <div className="nav-links">
          {tabs.map(tab => (
            <button key={tab.id} className={activeTab === tab.id ? 'active' : ''} onClick={() => setActiveTab(tab.id)}>
              {tab.label}
            </button>
          ))}
        </div>
      </nav>
      <div className="page-content">
                {activeTab === 'adcopy' && <AdCopyGenerator />}
        {activeTab === 'productdesc' && <ProductDescGenerator />}
        {activeTab === 'slogan' && <SloganGenerator />}
        {activeTab === 'caption' && <CaptionGenerator />}
        {activeTab === 'hashtag' && <HashtagGenerator />}
        {activeTab === 'seo' && <SEOWriter />}
        {activeTab === 'email' && <EmailWriter />}
        {activeTab === 'competitor' && <CompetitorAnalysis />}
        {activeTab === 'image' && <ImageGenerator />}
        {activeTab === 'landing' && <LandingPageBuilder />}
        {activeTab === 'scheduler' && <Scheduler />}
        {activeTab === 'analytics' && <Analytics />}
        {activeTab === 'history' && <History />}
      </div>
    </div>
  )
}

function CaptionGenerator() {
  const [topic, setTopic] = useState('')
  const [tone, setTone] = useState('exciting')
  const [platform, setPlatform] = useState('Instagram')
  const [caption, setCaption] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    if (!topic.trim()) { setError('Please enter a topic!'); return }
    setLoading(true); setError(''); setCaption('')
    try {
      const res = await fetch(API_BASE + '/api/generate-caption', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic, tone: tone, platform: platform })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Error')
      setCaption(data.caption)
    } catch (err) {
      setError('Failed to generate. Check backend server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h1>✨ AI Caption Generator</h1>
      <p className="subtitle">Generate engaging social media captions instantly</p>
      <div className="form-group">
        <label>Topic / Description</label>
        <input type="text" placeholder="e.g. new coffee shop opening" value={topic} onChange={(e) => setTopic(e.target.value)} />
      </div>
      <div className="form-row">
        <div className="form-group">
          <label>Tone</label>
          <select value={tone} onChange={(e) => setTone(e.target.value)}>
            <option value="exciting">Exciting</option>
            <option value="professional">Professional</option>
            <option value="funny">Funny</option>
            <option value="casual">Casual</option>
            <option value="inspirational">Inspirational</option>
          </select>
        </div>
        <div className="form-group">
          <label>Platform</label>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
            <option value="Instagram">Instagram</option>
            <option value="Facebook">Facebook</option>
            <option value="Twitter">Twitter/X</option>
            <option value="LinkedIn">LinkedIn</option>
          </select>
        </div>
      </div>
      <button className="generate-btn" onClick={generate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Caption ✨'}
      </button>
      {error && <p className="error">{error}</p>}
      {caption && (
        <div className="result-box">
          <h3>Your Caption:</h3>
          <p>{caption}</p>
          <button className="copy-btn" onClick={() => { navigator.clipboard.writeText(caption); alert('Copied!') }}>📋 Copy</button>
        </div>
      )}
    </div>
  )
}

function HashtagGenerator() {
  const [topic, setTopic] = useState('')
  const [hashtags, setHashtags] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    if (!topic.trim()) { setError('Please enter a topic!'); return }
    setLoading(true); setError(''); setHashtags('')
    try {
      const res = await fetch(API_BASE + '/api/generate-hashtags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Error')
      setHashtags(data.hashtags)
    } catch (err) {
      setError('Failed to generate. Check backend server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h1>🏷️ Hashtag Generator</h1>
      <p className="subtitle">Get trending hashtags for your content</p>
      <div className="form-group">
        <label>Topic / Description</label>
        <input type="text" placeholder="e.g. fitness motivation" value={topic} onChange={(e) => setTopic(e.target.value)} />
      </div>
      <button className="generate-btn" onClick={generate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Hashtags 🏷️'}
      </button>
      {error && <p className="error">{error}</p>}
      {hashtags && (
        <div className="result-box">
          <h3>Your Hashtags:</h3>
          <p>{hashtags}</p>
          <button className="copy-btn" onClick={() => { navigator.clipboard.writeText(hashtags); alert('Copied!') }}>📋 Copy</button>
        </div>
      )}
    </div>
  )
}

function SEOWriter() {
  const [keyword, setKeyword] = useState('')
  const [seoContent, setSeoContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    if (!keyword.trim()) { setError('Please enter a keyword!'); return }
    setLoading(true); setError(''); setSeoContent('')
    try {
      const res = await fetch(API_BASE + '/api/generate-seo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword: keyword })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Error')
      setSeoContent(data.seo_content)
    } catch (err) {
      setError('Failed to generate. Check backend server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h1>📝 SEO Writer</h1>
      <p className="subtitle">Generate SEO-optimized titles and descriptions</p>
      <div className="form-group">
        <label>Target Keyword</label>
        <input type="text" placeholder="e.g. best coffee shop in Austin" value={keyword} onChange={(e) => setKeyword(e.target.value)} />
      </div>
      <button className="generate-btn" onClick={generate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate SEO Content 📝'}
      </button>
      {error && <p className="error">{error}</p>}
      {seoContent && (
        <div className="result-box">
          <h3>SEO Content:</h3>
          <p>{seoContent}</p>
          <button className="copy-btn" onClick={() => { navigator.clipboard.writeText(seoContent); alert('Copied!') }}>📋 Copy</button>
        </div>
      )}
    </div>
  )
}

function EmailWriter() {
  const [purpose, setPurpose] = useState('')
  const [product, setProduct] = useState('')
  const [emailContent, setEmailContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    if (!purpose.trim() || !product.trim()) { setError('Please fill both fields!'); return }
    setLoading(true); setError(''); setEmailContent('')
    try {
      const res = await fetch(API_BASE + '/api/generate-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ purpose: purpose, product: product })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Error')
      setEmailContent(data.email_content)
    } catch (err) {
      setError('Failed to generate. Check backend server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h1>📧 Email Marketing Writer</h1>
      <p className="subtitle">Generate professional marketing emails instantly</p>
      <div className="form-group">
        <label>Email Purpose</label>
        <input type="text" placeholder="e.g. announce a discount sale" value={purpose} onChange={(e) => setPurpose(e.target.value)} />
      </div>
      <div className="form-group">
        <label>Product / Service</label>
        <input type="text" placeholder="e.g. handmade candles" value={product} onChange={(e) => setProduct(e.target.value)} />
      </div>
      <button className="generate-btn" onClick={generate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Email 📧'}
      </button>
      {error && <p className="error">{error}</p>}
      {emailContent && (
        <div className="result-box">
          <h3>Your Email:</h3>
          <p>{emailContent}</p>
          <button className="copy-btn" onClick={() => { navigator.clipboard.writeText(emailContent); alert('Copied!') }}>📋 Copy</button>
        </div>
      )}
    </div>
  )
}

function CompetitorAnalysis() {
  const [business, setBusiness] = useState('')
  const [competitor, setCompetitor] = useState('')
  const [analysis, setAnalysis] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    if (!business.trim() || !competitor.trim()) { setError('Please fill both fields!'); return }
    setLoading(true); setError(''); setAnalysis('')
    try {
      const res = await fetch(API_BASE + '/api/competitor-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ business: business, competitor: competitor })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Error')
      setAnalysis(data.analysis)
    } catch (err) {
      setError('Failed to generate. Check backend server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h1>🔍 Competitor Analysis</h1>
      <p className="subtitle">Get AI-powered insights on your competition</p>
      <div className="form-group">
        <label>Your Business</label>
        <input type="text" placeholder="e.g. local coffee shop" value={business} onChange={(e) => setBusiness(e.target.value)} />
      </div>
      <div className="form-group">
        <label>Competitor</label>
        <input type="text" placeholder="e.g. Starbucks" value={competitor} onChange={(e) => setCompetitor(e.target.value)} />
      </div>
      <button className="generate-btn" onClick={generate} disabled={loading}>
        {loading ? 'Analyzing...' : 'Analyze Competitor 🔍'}
      </button>
      {error && <p className="error">{error}</p>}
      {analysis && (
        <div className="result-box">
          <h3>Analysis:</h3>
          <p>{analysis}</p>
          <button className="copy-btn" onClick={() => { navigator.clipboard.writeText(analysis); alert('Copied!') }}>📋 Copy</button>
        </div>
      )}
    </div>
  )
}

function ImageGenerator() {
  const [prompt, setPrompt] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    if (!prompt.trim()) { setError('Please enter a prompt!'); return }
    setLoading(true); setError(''); setImageUrl('')
    try {
      const res = await fetch(API_BASE + '/api/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Error')
      setImageUrl(data.image_url)
    } catch (err) {
      setError('Failed to generate. Check backend server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h1>🖼️ Image Generator</h1>
      <p className="subtitle">Generate images from text prompts</p>
      <div className="form-group">
        <label>Prompt</label>
        <input type="text" placeholder="e.g. a cozy handmade candle on a wooden table" value={prompt} onChange={(e) => setPrompt(e.target.value)} />
      </div>
      <button className="generate-btn" onClick={generate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Image 🖼️'}
      </button>
      {error && <p className="error">{error}</p>}
      {imageUrl && (
        <div className="result-box">
          <h3>Your Image:</h3>
          <img src={imageUrl} alt="Generated" style={{ width: '100%', borderRadius: '8px', marginTop: '12px' }} />
        </div>
      )}
    </div>
  )
}

function LandingPageBuilder() {
  const [businessName, setBusinessName] = useState('')
  const [description, setDescription] = useState('')
  const [htmlContent, setHtmlContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [view, setView] = useState('preview')

  const generate = async () => {
    if (!businessName.trim() || !description.trim()) { setError('Please fill both fields!'); return }
    setLoading(true); setError(''); setHtmlContent('')
    try {
      const res = await fetch(API_BASE + '/api/generate-landing-page', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ business_name: businessName, description: description })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Error')
      setHtmlContent(data.html_content)
    } catch (err) {
      setError('Failed to generate. Check backend server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card wide-card">
      <h1>🌐 Landing Page Builder</h1>
      <p className="subtitle">Generate a complete landing page for your business</p>
      <div className="form-group">
        <label>Business Name</label>
        <input type="text" placeholder="e.g. Cozy Candle Co." value={businessName} onChange={(e) => setBusinessName(e.target.value)} />
      </div>
      <div className="form-group">
        <label>Business Description</label>
        <textarea rows="3" placeholder="e.g. We sell handmade soy candles with natural scents, made in small batches" value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      <button className="generate-btn" onClick={generate} disabled={loading}>
        {loading ? 'Building page...' : 'Generate Landing Page 🌐'}
      </button>
      {error && <p className="error">{error}</p>}
      {htmlContent && (
        <div className="result-box">
          <div className="form-row" style={{ marginBottom: '12px' }}>
            <button className={view === 'preview' ? 'active' : ''} onClick={() => setView('preview')}>Preview</button>
            <button className={view === 'code' ? 'active' : ''} onClick={() => setView('code')}>Code</button>
          </div>
          {view === 'preview' ? (
            <iframe
              title="Landing Page Preview"
              srcDoc={htmlContent}
              style={{ width: '100%', height: '500px', border: '1px solid #ddd', borderRadius: '8px' }}
            />
          ) : (
            <pre style={{ maxHeight: '500px', overflow: 'auto', background: '#1e1e1e', color: '#d4d4d4', padding: '12px', borderRadius: '8px', fontSize: '12px' }}>
              {htmlContent}
            </pre>
          )}
          <button className="copy-btn" onClick={() => { navigator.clipboard.writeText(htmlContent); alert('Copied!') }} style={{ marginTop: '12px' }}>📋 Copy HTML</button>
        </div>
      )}
    </div>
  )
}

function Scheduler() {
  const [content, setContent] = useState('')
  const [platform, setPlatform] = useState('Instagram')
  const [date, setDate] = useState('')
  const [posts, setPosts] = useState([])
  const [message, setMessage] = useState('')

  const fetchPosts = async () => {
    try {
      const res = await fetch(API_BASE + '/api/scheduled-posts')
      const data = await res.json()
      setPosts(data.posts || [])
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => { fetchPosts() }, [])

  const schedulePost = async () => {
    if (!content.trim() || !date) { setMessage('Please fill content and date!'); return }
    try {
      const res = await fetch(API_BASE + '/api/schedule-post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content, platform: platform, scheduled_date: date })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error)
      setMessage('✅ Post scheduled!')
      setContent(''); setDate('')
      fetchPosts()
    } catch (err) {
      setMessage('Failed to schedule post.')
    }
  }

  const deletePost = async (id) => {
    try {
      await fetch(API_BASE + '/api/scheduled-posts/' + id, { method: 'DELETE' })
      fetchPosts()
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="card wide-card">
      <h1>📅 Social Media Scheduler</h1>
      <p className="subtitle">Plan and schedule your posts across platforms</p>
      <div className="form-group">
        <label>Post Content</label>
        <textarea rows="3" placeholder="Write your post content..." value={content} onChange={(e) => setContent(e.target.value)} />
      </div>
      <div className="form-row">
        <div className="form-group">
          <label>Platform</label>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
            <option value="Instagram">Instagram</option>
            <option value="Facebook">Facebook</option>
            <option value="Twitter">Twitter/X</option>
            <option value="LinkedIn">LinkedIn</option>
          </select>
        </div>
        <div className="form-group">
          <label>Schedule Date</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </div>
      </div>
      <button className="generate-btn" onClick={schedulePost}>Schedule Post 📅</button>
      {message && <p className="info-msg">{message}</p>}
      <div className="posts-list">
        <h3>Upcoming Posts ({posts.length})</h3>
        {posts.length === 0 && <p className="empty-msg">No scheduled posts yet.</p>}
        {posts.map((post) => (
          <div key={post.id} className="post-item">
            <div>
              <span className="post-platform">{post.platform}</span>
              <span className="post-date">{post.scheduled_date}</span>
              <p>{post.content}</p>
            </div>
            <button className="delete-btn" onClick={() => deletePost(post.id)}>🗑️</button>
          </div>
        ))}
      </div>
    </div>
  )
}

function Analytics() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch(API_BASE + '/api/analytics')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error(err))
  }, [])

  if (!stats) return <div className="card"><p>Loading analytics...</p></div>

  const barWidth = (value) => {
    const pct = Math.min(value * 10, 100)
    return { width: pct + '%' }
  }

  return (
    <div className="card wide-card">
      <h1>📊 Analytics Dashboard</h1>
      <p className="subtitle">Track your content generation activity</p>
      <div className="stats-grid">
        <div className="stat-box">
          <h2>{stats.total_generated}</h2>
          <p>Total Content Generated</p>
        </div>
        <div className="stat-box">
          <h2>{stats.total_scheduled}</h2>
          <p>Posts Scheduled</p>
        </div>
      </div>
      <h3>Breakdown by Type</h3>
      <div className="breakdown">
        <div className="bar-row">
          <span>Captions</span>
          <div className="bar"><div className="bar-fill" style={barWidth(stats.breakdown.captions)}></div></div>
          <span>{stats.breakdown.captions}</span>
        </div>
        <div className="bar-row">
          <span>Hashtags</span>
          <div className="bar"><div className="bar-fill" style={barWidth(stats.breakdown.hashtags)}></div></div>
          <span>{stats.breakdown.hashtags}</span>
        </div>
        <div className="bar-row">
          <span>SEO Content</span>
          <div className="bar"><div className="bar-fill" style={barWidth(stats.breakdown.seo)}></div></div>
          <span>{stats.breakdown.seo}</span>
        </div>
        <div className="bar-row">
          <span>Emails</span>
          <div className="bar"><div className="bar-fill" style={barWidth(stats.breakdown.emails)}></div></div>
          <span>{stats.breakdown.emails}</span>
        </div>
        <div className="bar-row">
          <span>Competitor</span>
          <div className="bar"><div className="bar-fill" style={barWidth(stats.breakdown.competitor)}></div></div>
          <span>{stats.breakdown.competitor}</span>
        </div>
      </div>
    </div>
  )
}

function History() {
  const [history, setHistory] = useState([])

  useEffect(() => {
    fetch(API_BASE + '/api/history')
      .then(res => res.json())
      .then(data => setHistory(data.history || []))
      .catch(err => console.error(err))
  }, [])

  return (
    <div className="card wide-card">
      <h1>🕐 History</h1>
      <p className="subtitle">All your generated content</p>
      {history.length === 0 && <p className="empty-msg">No history yet. Generate some content first!</p>}
      <div className="history-list">
        {history.map((item) => (
          <div key={item.id} className="history-item">
            <span className={'history-tag tag-' + item.type}>{item.type}</span>
            <p className="history-input">Input: {item.input_text}</p>
            <p className="history-output">{item.output_text}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
function AdCopyGenerator() {
  const [product, setProduct] = useState('')
  const [platform, setPlatform] = useState('Google Ads')
  const [adCopy, setAdCopy] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    if (!product.trim()) { setError('Please enter a product!'); return }
    setLoading(true); setError(''); setAdCopy('')
    try {
      const res = await fetch(API_BASE + '/api/generate-ad-copy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product: product, platform: platform })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Error')
      setAdCopy(data.ad_copy)
    } catch (err) {
      setError('Failed to generate. Check backend server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h1>📢 Ad Copy Generator</h1>
      <p className="subtitle">Generate persuasive ad copy for your campaigns</p>
      <div className="form-group">
        <label>Product / Service</label>
        <input type="text" placeholder="e.g. wireless earbuds" value={product} onChange={(e) => setProduct(e.target.value)} />
      </div>
      <div className="form-group">
        <label>Ad Platform</label>
        <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
          <option value="Google Ads">Google Ads</option>
          <option value="Facebook Ads">Facebook Ads</option>
          <option value="Instagram Ads">Instagram Ads</option>
          <option value="LinkedIn Ads">LinkedIn Ads</option>
        </select>
      </div>
      <button className="generate-btn" onClick={generate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Ad Copy 📢'}
      </button>
      {error && <p className="error">{error}</p>}
      {adCopy && (
        <div className="result-box">
          <h3>Your Ad Copy:</h3>
          <p>{adCopy}</p>
          <button className="copy-btn" onClick={() => { navigator.clipboard.writeText(adCopy); alert('Copied!') }}>📋 Copy</button>
        </div>
      )}
    </div>
  )
}

function ProductDescGenerator() {
  const [productName, setProductName] = useState('')
  const [features, setFeatures] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    if (!productName.trim()) { setError('Please enter a product name!'); return }
    setLoading(true); setError(''); setDescription('')
    try {
      const res = await fetch(API_BASE + '/api/generate-product-description', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_name: productName, features: features })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Error')
      setDescription(data.description)
    } catch (err) {
      setError('Failed to generate. Check backend server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h1>🛍️ Product Description Generator</h1>
      <p className="subtitle">Create compelling e-commerce product descriptions</p>
      <div className="form-group">
        <label>Product Name</label>
        <input type="text" placeholder="e.g. Leather Laptop Backpack" value={productName} onChange={(e) => setProductName(e.target.value)} />
      </div>
      <div className="form-group">
        <label>Key Features (optional)</label>
        <input type="text" placeholder="e.g. waterproof, USB charging port, 15L capacity" value={features} onChange={(e) => setFeatures(e.target.value)} />
      </div>
      <button className="generate-btn" onClick={generate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Description 🛍️'}
      </button>
      {error && <p className="error">{error}</p>}
      {description && (
        <div className="result-box">
          <h3>Product Description:</h3>
          <p>{description}</p>
          <button className="copy-btn" onClick={() => { navigator.clipboard.writeText(description); alert('Copied!') }}>📋 Copy</button>
        </div>
      )}
    </div>
  )
}

function SloganGenerator() {
  const [businessName, setBusinessName] = useState('')
  const [industry, setIndustry] = useState('')
  const [slogans, setSlogans] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    if (!businessName.trim()) { setError('Please enter a business name!'); return }
    setLoading(true); setError(''); setSlogans('')
    try {
      const res = await fetch(API_BASE + '/api/generate-slogan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ business_name: businessName, industry: industry })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Error')
      setSlogans(data.slogans)
    } catch (err) {
      setError('Failed to generate. Check backend server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h1>💡 Brand Slogan Generator</h1>
      <p className="subtitle">Generate catchy taglines for your brand</p>
      <div className="form-group">
        <label>Business Name</label>
        <input type="text" placeholder="e.g. BrewHouse Coffee" value={businessName} onChange={(e) => setBusinessName(e.target.value)} />
      </div>
      <div className="form-group">
        <label>Industry</label>
        <input type="text" placeholder="e.g. coffee shop / cafe" value={industry} onChange={(e) => setIndustry(e.target.value)} />
      </div>
      <button className="generate-btn" onClick={generate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Slogans 💡'}
      </button>
      {error && <p className="error">{error}</p>}
      {slogans && (
        <div className="result-box">
          <h3>Your Slogans:</h3>
          <p>{slogans}</p>
          <button className="copy-btn" onClick={() => { navigator.clipboard.writeText(slogans); alert('Copied!') }}>📋 Copy</button>
        </div>
      )}
    </div>
  )
}