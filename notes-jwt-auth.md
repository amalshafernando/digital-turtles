1. Endpoints ක්‍රියාත්මක වන අනුපිළිවෙළ (Order of Endpoints Working)
Assessment brief එකට අනුව Customer page (name, email, message සමඟ support message යැවීම) සහ Team page (සරල login එකකට පිටුපසින් tickets බැලීම, category අනුව filter කිරීම, සහ status වෙනස් කිරීම) සඳහා strict/fixed endpoint execution order එකක් නැත. එහෙත් තාර්කික සහ සුමට ක්‍රියාකාරිත්වය (logical flow) සඳහා පහත අනුපිළිවෙළ වඩාත් සුදුසුය: 
1.	Health Check (GET /health): App එක සහ database/model readiness පරීක්ෂා කිරීමට (Docker healthcheck හෝ monitoring සඳහා).
2.	Public Ticket Creation (POST /tickets):
o	Customer form එකෙන් එන name, email, සහ message validate කරයි. 
o	ML classifier run කර category (සහ priority) predict කරයි. 
o	Grounded AI reply draft (සහ cited_faq_ids) සකස් කරයි. 
o	Ticket එක database එකේ save කර (status = "open" වැනි default අගයකින්) response එක ලබා දෙයි. 
3.	Team Login (POST /auth/login):
o	Team member කෙනෙකුගේ credentials verify කර JWT access token එකක් ලබා දෙයි. 
4.	Protected Team Endpoints (Valid JWT Token අවශ්‍ය වේ):
o	GET /tickets?category=...: Tickets ලැයිස්තුව ලබා ගැනීම සහ category අනුව filter කිරීම. 
o	GET /tickets/{id}: තනි ticket එකක විස්තර, AI draft, සහ cited FAQs බැලීම. 
o	PATCH /tickets/{id}/status: Ticket එකේ status (උදා: open → in_progress → resolved / closed) update කිරීම. 
2. JWT Login සඳහා team-member නමින් User කෙනෙකු සෑදිය යුතුද?
. 
•	හොඳම ක්‍රමය: Database එකේ users table එකක් (හෝ startup seed script / environment config) මඟින් team member කෙනෙකු සාදන්න (උදා: email / username + hashed password + role: "team_member").
•	අවශ්‍ය නම් demo/test පහසුව සඳහා admin වැනි seed user කෙනෙකු startup එකේදී (idempotently — දැනටමත් සිටී නම් නැවත නොසාදන ලෙස) create කළ හැක.
•	ආරක්ෂක අවවාදය: Plain-text passwords code එකේ hardcode නොකර bcrypt හෝ argon2 මඟින් hash කර තබන්න; JWT signing secret එක environment variable (JWT_SECRET_KEY) එකකින් ලබා ගන්න (default fallback එකක් තිබුණත් production/repo තුළ secrets නොතබන්න). 
3. Login සඳහා JWT Authentication ක්‍රියා කරන ආකාරය
පියවරෙන් පියවර ක්‍රියාවලිය:
1.	Login Request (POST /auth/login):
o	Team member විසින් email (හෝ username) සහ password යවයි.
o	Backend එක database එකෙන් user ව සොයා, ලබා දුන් password එක database එකේ ඇති password hash සමඟ සසඳා බලයි.
2.	Token Creation:
o	Credentials නිවැරදි නම් backend එක payload එකක් සාදා (sub: user id/email, role: "team_member", exp: expiration timestamp, iat: issued at) secret key එකකින් sign කර JWT එකක් (header.payload.signature) generate කර response එක ලෙස යවයි.
o	සටහන: JWT payload එක Base64URL encode වූවක් මිස encrypt වූවක් නොවන බැවින් passwords හෝ රහස්‍ය දත්ත payload එක තුළ නොතබන්න.
3.	Client Storage & Authenticated Requests:
o	Frontend team page එක එම token එක memory හෝ storage තුළ තබාගෙන, protected endpoints (GET /tickets, PATCH /tickets/{id}/status) call කරන විට HTTP header එකක් ලෙස යවයි:
Authorization: Bearer <your_jwt_token>
4.	Token Verification on Backend:
o	Protected endpoint එකකට request එකක් ආ විට auth dependency/middleware එක Bearer token එක extract කර:
	Signature එක valid දැයි පරීක්ෂා කරයි.
	exp (expiration time) ඉක්මවා ගොස් නැති බව තහවුරු කරයි.
	User/role (team_member) authorized දැයි බලයි.
o	Token එක valid නැතිනම් හෝ expire වී ඇත්නම් 401 Unauthorized return කරයි.
4. Assessment Context සඳහා Practical Note (Timebox & Trade-off)
•	මෙම take-home task එක පැය 4–5ක කාලයකට සීමා වන බැවින්, FastAPI + PyJWT (or python-jose) + passlib/pwdlib සමඟ සරල, පැහැදිලි JWT login flow එකක් සෑදීම ඉතා සුදුසුය (refresh tokens, OAuth2 providers, හෝ complex RBAC වැනි අමතර දේවලට වැඩි කාලයක් වැය නොකර). 

