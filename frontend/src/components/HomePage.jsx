import React, { useState } from 'react';
import './HomePage.css';

// CSUCI logo mark used in the masthead and footer
function BrandMark() {
  return (
    <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
      <circle cx="17" cy="17" r="16" fill="#2F2F2F" />
      <path d="M17 6l4 12h-8l4-12z" fill="#CB132A" />
      <rect x="14" y="18" width="6" height="9" fill="#D9D9D6" />
      <rect x="8" y="27" width="18" height="2" fill="#CB132A" />
    </svg>
  );
}

function HomePage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = () => setMenuOpen(false);

  return (
    <div className="ci-home">
      <a className="skip" href="#main">Skip to main content</a>

      {/* Utility bar */}
      <div className="util">
        <div className="wrap">
          <a href="#">Current Students</a>
          <a href="#">Faculty &amp; Staff</a>
          <a href="#">Alumni</a>
          <a href="#">Give</a>
          <a href="#">Search</a>
        </div>
      </div>

      {/* Masthead */}
      <header className="masthead">
        <div className="wrap">
          <a className="brand" href="#">
            <BrandMark />
            <span className="brandtext">
              <b>CSU Channel Islands</b>
              <span>University &middot; Est. 2002</span>
            </span>
          </a>

          <button
            className="menu-toggle"
            aria-expanded={menuOpen}
            aria-controls="primary-nav"
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? 'Close' : 'Menu'}
          </button>

          <nav className={`nav ${menuOpen ? 'open' : ''}`} id="primary-nav" aria-label="Primary">
            <a href="#academics" onClick={closeMenu}>Academics</a>
            <a href="#admissions" onClick={closeMenu}>Admissions</a>
            <a href="#campus" onClick={closeMenu}>Campus Life</a>
            <a href="#news" onClick={closeMenu}>News</a>
            <a href="#about" onClick={closeMenu}>About</a>
            <a className="btn btn-apply" href="#admissions" onClick={closeMenu}>Apply now</a>
          </nav>
        </div>
      </header>

      <main id="main">
        {/* Hero */}
        <section className="hero">
          <div className="hero-art" aria-hidden="true">
            <svg viewBox="0 0 1440 220" preserveAspectRatio="none">
              <path d="M0,120 C240,60 420,180 720,130 C980,88 1180,170 1440,110 L1440,220 L0,220 Z" fill="#242424" />
              <path d="M0,160 C260,110 480,200 760,160 C1020,124 1220,196 1440,150 L1440,220 L0,220 Z" fill="#171717" opacity=".85" />
            </svg>
          </div>
          <div className="wrap">
            <p className="eyebrow">Fall 2026 applications are open</p>
            <h1>Learn where the coast <em>meets</em> the classroom.</h1>
            <p>A public university on the water, built for students who want small classes, real research, and a degree that goes to work on day one.</p>
            <div className="hero-actions">
              <a className="btn btn-apply" href="#admissions">Start your application</a>
              <a className="btn btn-ghost" href="#campus">Visit campus</a>
            </div>
          </div>
        </section>

        {/* Signature: today strip */}
        <div className="wrap">
          <div className="today">
            <p className="today-label"><span className="dot"></span> Today on campus</p>
            <div className="today-items">
              <div><time>9:00 AM</time>Transfer advising drop-in &middot; Bell Tower 210</div>
              <div><time>12:30 PM</time>Research lab open tour &middot; Sierra Hall</div>
              <div><time>4:00 PM</time>Women&apos;s soccer vs. Cape Union &middot; North Field</div>
              <div><time>7:00 PM</time>Student film night &middot; Malibu Hall</div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <section className="stats">
          <div className="wrap stats-grid">
            <div className="stat"><b>7,400</b><span>Students enrolled</span></div>
            <div className="stat"><b>18:1</b><span>Student to faculty</span></div>
            <div className="stat"><b>62</b><span>Degree programs</span></div>
            <div className="stat"><b>91%</b><span>Employed or in grad school</span></div>
          </div>
        </section>

        {/* Programs */}
        <section className="section" id="academics">
          <div className="wrap">
            <div className="section-head">
              <p className="eyebrow">Academics</p>
              <h2>Six colleges. One campus small enough to know your name.</h2>
              <p>Undergraduate, graduate, and credential programs taught by faculty who advise, not just lecture.</p>
            </div>
            <div className="cards">
              <a className="card" href="#">
                <p className="eyebrow">14 majors</p>
                <h3>Science &amp; Environment</h3>
                <p>Marine biology, environmental science, and chemistry, with fieldwork that starts freshman year.</p>
                <p className="arrow">Explore programs &rarr;</p>
              </a>
              <a className="card" href="#">
                <p className="eyebrow">11 majors</p>
                <h3>Business &amp; Economics</h3>
                <p>Accounting, finance, and management, with a required internship in every track.</p>
                <p className="arrow">Explore programs &rarr;</p>
              </a>
              <a className="card" href="#">
                <p className="eyebrow">9 majors</p>
                <h3>Arts &amp; Humanities</h3>
                <p>Studio art, literature, history, and performance in a working-studio model.</p>
                <p className="arrow">Explore programs &rarr;</p>
              </a>
              <a className="card" href="#">
                <p className="eyebrow">8 majors</p>
                <h3>Engineering &amp; Computing</h3>
                <p>Software, mechanical, and coastal engineering, capped by a year-long senior design project.</p>
                <p className="arrow">Explore programs &rarr;</p>
              </a>
              <a className="card" href="#">
                <p className="eyebrow">10 majors</p>
                <h3>Health &amp; Nursing</h3>
                <p>Nursing, public health, and kinesiology, with clinical placements across the county.</p>
                <p className="arrow">Explore programs &rarr;</p>
              </a>
              <a className="card" href="#">
                <p className="eyebrow">10 majors</p>
                <h3>Education &amp; Social Sciences</h3>
                <p>Teaching credentials, psychology, and sociology, built around community partnerships.</p>
                <p className="arrow">Explore programs &rarr;</p>
              </a>
            </div>
          </div>
        </section>

        {/* News + Events */}
        <section className="section section-alt" id="news">
          <div className="wrap split">
            <div>
              <div className="section-head section-head-tight">
                <p className="eyebrow">News</p>
                <h2>What&apos;s happening at Channel Islands</h2>
              </div>

              <a className="story" href="#">
                <div className="thumb"></div>
                <div>
                  <time>July 9, 2026</time>
                  <h3>Marine lab tracks record kelp recovery along the north shore</h3>
                  <p className="story-blurb">Three years of student-collected data show the reef bouncing back faster than models predicted.</p>
                </div>
              </a>

              <a className="story" href="#">
                <div className="thumb"></div>
                <div>
                  <time>July 2, 2026</time>
                  <h3>New scholarship covers full tuition for county transfer students</h3>
                  <p className="story-blurb">The Dolphin Promise opens to applicants with an associate degree beginning this fall.</p>
                </div>
              </a>

              <a className="story" href="#">
                <div className="thumb"></div>
                <div>
                  <time>June 24, 2026</time>
                  <h3>Engineering seniors design a low-cost tide gauge for coastal towns</h3>
                  <p className="story-blurb">The team&apos;s open-source sensor is already deployed at four harbors along the coast.</p>
                </div>
              </a>

              <p className="more-link"><a href="#">All news &rarr;</a></p>
            </div>

            <aside className="events">
              <p className="eyebrow" style={{ marginBottom: '16px' }}>Upcoming events</p>

              <div className="event">
                <div className="date"><b>18</b><span>Jul</span></div>
                <div>
                  <h4>Summer commencement</h4>
                  <p>10:00 AM &middot; South Quad</p>
                </div>
              </div>
              <div className="event">
                <div className="date"><b>25</b><span>Jul</span></div>
                <div>
                  <h4>Preview day for admitted students</h4>
                  <p>9:00 AM &middot; Bell Tower</p>
                </div>
              </div>
              <div className="event">
                <div className="date"><b>02</b><span>Aug</span></div>
                <div>
                  <h4>Coastal research symposium</h4>
                  <p>1:00 PM &middot; Sierra Hall</p>
                </div>
              </div>
              <div className="event">
                <div className="date"><b>19</b><span>Aug</span></div>
                <div>
                  <h4>Move-in week begins</h4>
                  <p>All day &middot; Residence halls</p>
                </div>
              </div>

              <p className="more-link" style={{ marginTop: '20px' }}><a href="#">Full calendar &rarr;</a></p>
            </aside>
          </div>
        </section>

        {/* CTA */}
        <section className="cta" id="admissions">
          <div className="wrap">
            <div>
              <p className="eyebrow">Admissions</p>
              <h2>Applications for Fall 2026 close November 30.</h2>
            </div>
            <div className="hero-actions">
              <a className="btn btn-apply" href="#">Apply now</a>
              <a className="btn btn-ghost" href="#">Request information</a>
            </div>
          </div>
        </section>

        {/* Campus life */}
        <section className="section" id="campus">
          <div className="wrap">
            <div className="section-head">
              <p className="eyebrow">Campus life</p>
              <h2>A thousand acres between the hills and the harbor.</h2>
              <p>Residence halls, 40 student organizations, intercollegiate athletics, and a working shoreline that doubles as a classroom.</p>
            </div>
            <div className="cards">
              <a className="card" href="#"><h3>Housing &amp; dining</h3><p>Six residence communities, all within a ten-minute walk of the heart of campus.</p><p className="arrow">See housing &rarr;</p></a>
              <a className="card" href="#"><h3>Clubs &amp; organizations</h3><p>From the sailing team to the robotics club, find your people in week one.</p><p className="arrow">Browse clubs &rarr;</p></a>
              <a className="card" href="#"><h3>Athletics</h3><p>Varsity teams competing as the CSUCI Dolphins.</p><p className="arrow">Game schedule &rarr;</p></a>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer id="about">
        <div className="wrap">
          <div className="fgrid">
            <div className="fcol">
              <a className="brand" href="#">
                <BrandMark />
                <span>
                  <b>CSU Channel Islands</b>
                  <span>University &middot; Est. 2002</span>
                </span>
              </a>
              <address>
                One University Drive<br />
                Camarillo, CA 93012<br />
                (805) 437-8400
              </address>
            </div>

            <div className="fcol">
              <h5>Academics</h5>
              <ul>
                <li><a href="#">Majors &amp; minors</a></li>
                <li><a href="#">Graduate programs</a></li>
                <li><a href="#">Library</a></li>
                <li><a href="#">Academic calendar</a></li>
              </ul>
            </div>

            <div className="fcol">
              <h5>Admissions</h5>
              <ul>
                <li><a href="#">Apply</a></li>
                <li><a href="#">Tuition &amp; aid</a></li>
                <li><a href="#">Visit campus</a></li>
                <li><a href="#">Transfer students</a></li>
              </ul>
            </div>

            <div className="fcol">
              <h5>Resources</h5>
              <ul>
                <li><a href="#">Student portal</a></li>
                <li><a href="#">Campus safety</a></li>
                <li><a href="#">Accessibility</a></li>
                <li><a href="#">Careers</a></li>
              </ul>
            </div>
          </div>

          <div className="legal">
            <p>&copy; 2026 California State University Channel Islands.</p>
            <p><a href="#">Privacy</a> &middot; <a href="#">Terms</a> &middot; <a href="#">Title IX</a></p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default HomePage;
