import { useState, type CSSProperties } from "react";
import Rain from "./components/Rain";

const domain = "thatguy.in".split("");
const name = "BHAVYAM".split("");
const tilts = [-7, 4, -3, 7, -5, 3, -6];
const rises = [3, -3, 2, -4, 3, -2, 1];

function GithubIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M9 19c-4.3 1.3-4.3-2.2-6-2.7m12 5v-3.5a3 3 0 0 0-.8-2.3c2.8-.3 5.8-1.4 5.8-6.3A4.9 4.9 0 0 0 18.7 6a4.5 4.5 0 0 0-.1-3.2s-1.1-.4-3.6 1.3a12.4 12.4 0 0 0-6 0C6.5 2.4 5.4 2.8 5.4 2.8A4.5 4.5 0 0 0 5.3 6 4.9 4.9 0 0 0 4 9.3c0 4.9 3 6 5.8 6.3a3 3 0 0 0-.8 2.2v3.5"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function LinkedinIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect
        x="3"
        y="3"
        width="18"
        height="18"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <path
        d="M7.5 10.5v6M11.5 16.5v-6m0 2.5c0-3.4 5-3.4 5 0v3.5"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="7.5" cy="7.5" r="1" fill="currentColor" />
    </svg>
  );
}

function InstagramIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect
        x="3"
        y="3"
        width="18"
        height="18"
        rx="5"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.7" />
      <circle cx="17.5" cy="6.5" r="1" fill="currentColor" />
    </svg>
  );
}

const socials = [
  {
    name: "GitHub",
    url: "https://github.com/bhavyam2468",
    Icon: GithubIcon,
  },
  {
    name: "LinkedIn",
    url: "https://www.linkedin.com/in/bhavyamdawra/",
    Icon: LinkedinIcon,
  },
  {
    name: "Instagram",
    url: "https://www.instagram.com/bhavyam_dawra/",
    Icon: InstagramIcon,
  },
];

export default function App() {
  const [hovered, setHovered] = useState(false);
  const [pinned, setPinned] = useState(false);
  const revealed = hovered || pinned;

  return (
    <main className="scene" aria-label="Bhavyam Dawra's portfolio, under construction">
      <div className="scene__artwork" aria-hidden="true">
        <img
          className="scene__image"
          src="/images/quiet-street.jpg"
          alt=""
          fetchPriority="high"
          draggable="false"
        />
        <div className="scene__shade" />
        <Rain />
        <div className="scene__vignette" />
      </div>

      <div className="ribbons">
        <div className="ribbon ribbon--rear" aria-hidden="true">
          <div className="ribbon__print">
            {Array.from({ length: 9 }, (_, index) => (
              <span className="ribbon__repeat" key={index}>
                <span className="ribbon__mini-checker" />
                <span>Site under construction</span>
              </span>
            ))}
          </div>
        </div>

        <div className="ribbon ribbon--main">
          <div className="ribbon__inner">
            <span className="ribbon__checker ribbon__checker--left" aria-hidden="true" />
            <h1 className={`wordmark${revealed ? " is-revealed" : ""}`}>
              <button
                className="wordmark__button"
                type="button"
                aria-label="thatguy.in. Tap to reveal Bhavyam Dawra."
                aria-pressed={pinned}
                onPointerEnter={(event) => {
                  if (event.pointerType === "mouse" || event.pointerType === "pen") {
                    setHovered(true);
                  }
                }}
                onPointerLeave={() => setHovered(false)}
                onClick={() => setPinned((previous) => !previous)}
                onBlur={() => setPinned(false)}
                onKeyDown={(event) => {
                  if (event.key === "Escape") {
                    setPinned(false);
                    setHovered(false);
                  }
                }}
              >
                <span className="wordmark__domain" aria-hidden="true">
                  {domain.map((letter, index) => (
                    <span
                      className="wordmark__domain-glyph"
                      style={{ "--index": index } as CSSProperties}
                      key={`${letter}-${index}`}
                    >
                      {letter}
                    </span>
                  ))}
                </span>
                <span className="wordmark__identity" aria-hidden="true">
                  {name.map((letter, index) => (
                    <span
                      className="wordmark__identity-glyph"
                      style={
                        {
                          "--index": index,
                          "--tilt": `${tilts[index]}deg`,
                          "--rise": `${rises[index]}px`,
                        } as CSSProperties
                      }
                      key={`${letter}-${index}`}
                    >
                      {letter}
                    </span>
                  ))}
                </span>
              </button>
            </h1>
            <span className="ribbon__checker ribbon__checker--right" aria-hidden="true" />
          </div>
        </div>
      </div>

      <section className="scene-message" aria-label="In the meantime">
        <p className="scene-message__headline">A little work in progress.</p>
        <nav className="socials" aria-label="Find Bhavyam online">
          {socials.map(({ name: socialName, url, Icon }) => (
            <a
              className="social-link"
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`${socialName} (opens in a new tab)`}
              key={socialName}
            >
              <Icon />
              <span className="social-link__label" aria-hidden="true">
                {socialName}
              </span>
            </a>
          ))}
        </nav>
      </section>

      <div className="scene__grain" aria-hidden="true" />
    </main>
  );
}
