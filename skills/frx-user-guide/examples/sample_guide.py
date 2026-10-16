"""Worked example: a guide for "Order Desk", a made-up order dashboard (8 pages), built on guide_lib.

    python3 sample_guide.py <img_dir> <out.docx>

img_dir holds the annotated PNGs (01_orders.png ...). Missing images are drawn as grey placeholders, so the
example builds with an empty folder. Copy this file next to your work, rename, and replace the content.
Keep the shape: plan() -> cover() -> one g.page() per TOC row. Real guides use real annotated screenshots.
"""
import os
import sys

# SK = the skill's base directory (personal skill or installed plugin); works from any copy of this file
SK = os.environ.get('SK') or os.path.expanduser('~/.claude/skills/frx-user-guide/skills/frx-user-guide')
sys.path.insert(0, os.path.join(SK, 'scripts'))
from guide_lib import (Guide, bullet, callout, cap, data_table, label, note, numbered, p, qa,  # noqa: E402
                       subheading)

IMG_DIR, OUT = sys.argv[1], sys.argv[2]
IMAGES = {'01_orders.png': (2400, 1500), '02_order.png': (2400, 1700), '03_reports.png': (2400, 1400),
          '04_alerts.png': (1800, 1200)}


def placeholders():
    """Grey stand-ins for screenshots that are not captured yet (example only)."""
    from PIL import Image, ImageDraw
    os.makedirs(IMG_DIR, exist_ok=True)
    for name, size in IMAGES.items():
        path = os.path.join(IMG_DIR, name)
        if not os.path.exists(path):
            im = Image.new('RGB', size, (236, 239, 237))
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, size[0] - 1, size[1] - 1), outline=(180, 186, 183), width=6)
            d.text((40, 40), f'Screenshot: {name}', fill=(90, 103, 97))
            im.save(path)


placeholders()
g = Guide('Order Desk', img_dir=IMG_DIR, date_label='October 2026')

g.plan([
    'Getting in and finding your way',
    'Orders list',
    'Order details',
    'Reports',
    'Alerts and notifications',
    'Roles and permissions',
    'FAQ',
])

g.cover([
    p('One board for every customer order: what came in, who is handling it and what is late.', sz=22),
    callout('Everyone can see every order; your role decides what you can change. Missing a button? See '
            f'page {g.pg("Roles and permissions")}.'),
    label('IN THIS GUIDE'),
    data_table(['Section', 'Page'], g.toc_rows(), [5670, 1134]),
], [
    subheading('Where the data comes from'),
    p('Orders arrive from the online store on their own. You add what only people know: notes, owners and priorities.'),
    data_table(['Source', 'What it feeds', 'Refreshes'], [
        ['Online store', 'Orders, customers, totals', 'Every 5 minutes'],
        ['Warehouse', 'Stock and shipping status', 'Every hour'],
        ['Reports', 'Daily and monthly summaries', 'Daily, 1:00 AM'],
    ], [1700, 2900, 2884]),
    note('Three things that hold everywhere:'),
    numbered(1, '**One sign-in.** Use your company account; there is no separate login.'),
    numbered(2, '**Fix data at the source.** Order lines and totals come from the store. Change them there.'),
    numbered(3, '**The link is the view.** Search, filters and sort are kept in the address bar. Copy the link and a '
                'teammate sees exactly what you see.'),
])

# 2 — basics (text + tables only, no screenshot)
g.page('BASICS', 'Getting in and finding your way', [
    p('Open Order Desk from the company portal. If you are not signed in, you go to the sign-in page first and '
      'come back here afterwards.'),
    label('IF YOU SEE A MESSAGE INSTEAD'),
    bullet('**No access:** your account is not on the user list yet. Ask an admin to add your email.'),
    bullet('**Can\'t reach the server:** your network dropped or the board is down. Click **Try again**.'),
    note('Your name and **Sign out** sit on the right of the top bar.'),
], [
    label('LEFT SIDEBAR'),
    data_table(['Item', 'What it opens', 'Who sees it (default)'], [
        ['Orders', f'Orders list (page {g.pg("Orders list")})', 'Everyone'],
        ['Reports', f'Daily and monthly summaries (page {g.pg("Reports")})', 'Manager, Admin'],
        ['Settings', f'Users and roles (page {g.pg("Roles and permissions")})', 'Admin'],
    ], [2700, 3400, 2558]),
    label('THE BELL'),
    bullet(f'Shows late orders and orders assigned to you (page {g.pg("Alerts and notifications")}).'),
], lw=6010, rw=9298)

# 3 — orders list
g.page('PAGES', 'Orders list', [
    p('**Orders** is the home page. It lists every order, 25 per page, newest first. Click a row to open the order.'),
    label('FIND AN ORDER'),
    bullet('**Search** matches the order number or the customer name as you type.'),
    bullet('**Status** starts on **Open**. Pick **All** to see shipped and cancelled orders too.'),
    bullet('**Sort** by clicking a header with arrows.'),
    label('READ THE BADGES'),
    data_table(['Badge', 'Meaning'], [
        ['LATE', 'Not shipped 2 days after the promised date.'],
        ['ON HOLD', 'Waiting for payment or stock.'],
        ['READY', 'Packed and waiting for pickup.'],
    ], [1700, 4310]),
    note('There is no export on this page. Share the link instead.'),
], [
    g.image('01_orders.png'),
    cap(1, '**+ New Order** for phone orders. Manager and Admin by default.'),
    cap(2, 'Search by order number or customer name.'),
    cap(3, 'Filters: Status, Owner, Channel. **Clear all filters** resets them.'),
    cap(4, 'Sortable column. Click again to reverse the order.'),
    cap(5, 'Status badge for each order.'),
])

# 4 — order details
g.page('PAGES', 'Order details', [
    p('Everything about one order: lines, customer, shipping and notes. Each card saves on its own.'),
    label('HOW TO HANDLE AN ORDER'),
    numbered(1, 'Click **Assign to me** so the team knows you have it.'),
    numbered(2, 'Check the lines and the shipping address.'),
    numbered(3, 'Click **Mark Ready** once it is packed.'),
    label('GOOD TO KNOW'),
    bullet('**Notes** are internal. Customers never see them.'),
    bullet('**Cancel Order** asks for a reason and cannot be undone.'),
    note('Cancel Order needs the cancel permission (Manager and Admin by default).'),
], [
    g.image('02_order.png'),
    cap(1, '**Assign to me** or pick another owner.'),
    cap(2, 'Order lines with quantity and price.'),
    cap(3, 'Shipping address and method.'),
    cap(4, '**Mark Ready** and **Cancel Order**.'),
], toc='Order details')

# 5 — reports
g.page('PAGES', 'Reports', [
    p('Totals for one day or one month, compared with the period before.'),
    label('READ THE TABLE'),
    data_table(['Column', 'Meaning'], [
        ['Orders', 'Orders placed in the period.'],
        ['Late %', 'Share of orders shipped after the promised date.'],
        ['vs Previous', '**Up** or **Down** against the period before.'],
    ], [1700, 4310]),
    note('Reports refresh daily at 1:00 AM. Needs the reports permission (Manager and Admin by default).'),
], [
    g.image('03_reports.png'),
    cap(1, 'Pick a day or a month.'),
    cap(2, 'Totals for the period.'),
    cap(3, '**Export** downloads the table as CSV.'),
])

# 6 — alerts (smaller image + a table under the captions)
g.page('SETTINGS', 'Alerts and notifications', [
    p('Choose which alerts reach you in the bell.'),
    label('TURN AN ALERT ON'),
    numbered(1, 'Open **Settings › Alerts**.'),
    numbered(2, 'Tick the alerts you want, then click **Save**.'),
], [
    g.image('04_alerts.png', max_cx=4200000),
    cap(1, 'Alert list with on/off ticks.'),
    cap(2, '**Save**.'),
    label('ALERT TYPES'),
    data_table(['Alert', 'When it fires'], [
        ['Order assigned', 'Someone assigns an order to you.'],
        ['Order late', 'One of your orders becomes LATE.'],
    ], [2600, 6358]),
])

# 7 — roles
Y, N = 'Yes', '—'
g.page('REFERENCE', 'Roles and permissions', [
    p('Everyone signed in sees every order. Your role decides what you can change.'),
    data_table(['Action', 'Admin', 'Manager', 'Staff'], [
        ['Create a phone order', Y, Y, N],
        ['Assign and mark ready', Y, Y, Y],
        ['Cancel an order', Y, Y, N],
        ['See reports', Y, Y, N],
        ['Manage users and roles', Y, N, N],
    ], [3210, 800, 1200, 800]),
    note('These are the default roles. An admin can change any role in Settings.'),
], [
    label('IF A NUMBER LOOKS WRONG'),
    numbered(1, 'Check **Last refreshed** on the page.'),
    numbered(2, 'Check the order in the online store.'),
    numbered(3, 'Still wrong? Send the order number and a screenshot to the support team.'),
])

# 8 — FAQ
FAQ = [
    ('I can\'t see a button from this guide.', f'Your role doesn\'t include it. See page {g.pg("Roles and permissions")}.'),
    ('An order shows LATE but it has shipped.', 'The warehouse status refreshes every hour. Check again after the next refresh.'),
    ('Can I undo Cancel Order?', 'No. Create a new order instead.'),
    ('Can I export the orders list?', 'No. Filter the list and share the link; the link keeps your filters.'),
]
half = (len(FAQ) + 1) // 2
g.page('REFERENCE', 'FAQ',
       [qa(q, a) for q, a in FAQ[:half]],
       [qa(q, a) for q, a in FAQ[half:]], lw=7371, rw=7938)

g.build(OUT)
