# from pandas.core.arrays.integer import Int32Dtype
import requests
from bs4 import BeautifulSoup
import pandas as pd

URL = 'https://saint-petersburg.irr.ru/real-estate/apartments-sale/'
HEADERS =  {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; rv:71.0) Gecko/20100101 Firefox/71.0',
            'accept': '*/*'}

# features:
# rooms (студия - 1)+, area+, lowest_floor, highest_floor, total_floors, 
# metro_station+, district, interior (remont), years, cost

def get_html(url, append=''):
    r = requests.get(url+append, headers=HEADERS)
    return r

def view_pages(links, liv_areas=[], districts=[], years=[], interiors=[], kitchen_areas=[], mins_to_metro=[], metro=[]):
    for l in links:
        page = get_html(l)
        s = BeautifulSoup(page.text, 'html.parser')
        items = s.find_all('li', class_='productPage__infoColumnBlockText')
        ch_l, ch_d, ch_y_future, ch_y, ch_i, ch_k, ch_mm, ch_m = 0, 0, 0, 0, 0, 0, 0, 0
        for i in items:
            i = str(i.get_text())
            #print(i)
            if 'Жилая площадь' in i:
                i = i.replace('Жилая площадь: ', '')
                i = float(i.replace(' м2', ''))
                liv_areas.append(i)
                ch_l = 1
            elif 'Район города' in i:
                i = i.replace('Район города: ', '')
                i = i[:(len(i)-1)]
                districts.append(i)
                ch_d = 1
            elif 'Год постройки/сдачи' in i:
                i = i.replace('Год постройки/сдачи: ', '')
                i = int(i.replace(' г.', ''))
                years.append(i)
                ch_y_future = 1
            elif 'Год постройки' in i:
                i = i.replace('Год постройки: ', '')
                i = int(i.replace(' г.', ''))
                years.append(i)
                ch_y = 1
            elif 'Ремонт' in i:
                i = i.replace('Ремонт: ', '')
                i = i[:(len(i)-1)]
                interiors.append(i)
                ch_i = 1
            elif 'Площадь кухни' in i:
                i = i.replace('Площадь кухни: ', '')
                i = float(i.replace(' м2', ''))
                kitchen_areas.append(i)
                ch_k = 1
            elif 'Метро' in i:
                i = i.replace('Метро: ', '')
                i = i.replace(' м.', '')
                metro.append(i)
                ch_m = 1
            elif 'До метро, минут(пешком)' in i:
                i = i.replace('До метро, минут(пешком): ', '')
                i = int(i.replace(' мин/пеш', ''))
                mins_to_metro.append(i)
                ch_mm = 1
        if ch_l == 0:
            liv_areas.append(None)
        if ch_d == 0:
            districts.append(None)
        if ch_y_future == 0 and ch_y == 0:
            years.append(None)
        if ch_i == 0:
            interiors.append(None)
        if ch_k == 0:
            kitchen_areas.append(None)
        if ch_m == 0:
            metro.append(None)
        if ch_mm == 0:
            mins_to_metro.append(None)
            #print(i)
            
    return liv_areas, districts, years, interiors, kitchen_areas, mins_to_metro, metro

def get_content(html):
    global df
    global id

    soup = BeautifulSoup(html.text, 'html.parser')
    rooms = soup.find_all('div', class_='js-productListingProductName')
    spans = soup.find_all('span')
    ars = soup.find_all('div', class_='listing__itemParameter')
    floors = soup.find_all('div', class_='listing__itemParameter js-cropRentParams')
    prs = soup.find_all('div', class_='listing__itemPrice')
    hrefs = soup.find_all('a', class_='listing__itemTitle', target='_blank')
    lowest_floors, highest_floors, metro, areas, links, prices = [], [], [], [], [], []

    for p in prs:
        try:
            p = p.get_text()
            p = p.replace('руб.', '')
            p = p.replace('\n\t', '')
            p = p.replace('\xa0', '')
            #print(p)
            p = int(p)
            prices.append(p)
        except:
            prices.append(None)

    for h in hrefs:
        links.append(h['href'])

    for f in floors:
        try:
            f = f.get_text()
            f = f.replace('эт. ', '')
            l, h = map(int, f.split(' / '))
            lowest_floors.append(l)
            highest_floors.append(h)
        except:
            lowest_floors.append(None)
            highest_floors.append(None)

    for a in ars:
        try:
            a = a.get_text()
            if ' м' in a:
                a = a.replace(' м', '')
                a = int(a) // 10
                areas.append(a)
        except:
            areas.append(None)

    #for m in spans:
    #    try:
    #        m = m.get_text()
    #        if 'м.' in m:
    #            if '\n' in m:
    #                m = m.replace('\n', '')
    #            m = m.replace(' м.', '')    
    #            metro.append(m)
    #    except:
    #        metro.append(None)

    liv_areas, districts, years, interiors, kitchen_areas, mins_to_metro, metro = view_pages(links)

    data = []
    
    for i in range(len(rooms)):
        row = {
            'rooms': rooms[i].get_text(),
            'area': areas[i],
            'metro': metro[i],
            'lowest_floor': lowest_floors[i],
            'highest_floor': highest_floors[i],
            'living_area': liv_areas[i],
            'district': districts[i],
            'year': years[i],
            'interior': interiors[i],
            'kitchen_area': kitchen_areas[i],
            'mins_to_metro': mins_to_metro[i],
            'price': prices[i],
            'link': links[i]
        }
        df = df.append(pd.DataFrame(row, index=[id]))
        id += 1
        data.append(row)
    
    #print(data[2])

    return data

def parse():
    data = []
    html = get_html(URL)
    soup = BeautifulSoup(html.text, 'html.parser')
    total_pages = int(soup.find_all('a', class_='pagination__pagesLink')[-1].get_text())
    if html.status_code == 200:
        # repeat for all pages of the website
        for i in range(1, total_pages+1):
            append = 'page' + str(i)
            html = get_html(URL, append=append)
            data += get_content(html)
            print('Page', i, 'iterated')
    else:
        print('Connection error')
    
    #print(data)
    return data

id = 0
df = pd.DataFrame({
    'rooms': [],
    'area': [],
    'metro': [],
    'lowest_floor': [],
    'highest_floor': [],
    'living_area': [],
    'district': [],
    'year': [],
    'interior': [],
    'kitchen_area': [],
    'mins_to_metro': [],
    'price': [],
    'link': []
})

data = parse()
print(df)
df.to_csv(r'C:\Users\Daniel\OneDrive\Документы\datasets\apartement_data.csv', index=False)
