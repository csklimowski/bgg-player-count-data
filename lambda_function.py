import json
import time
import sys
from xml.etree import ElementTree
from urllib.request import urlopen


def get_backoff(url):
    backoff_time = 0.1
    text = None
    while True:
        try:
            request = urlopen(url)
            text = request.read()
            request.close()
            break
        except e:
            if backoff_time > 1:
                raise e
            else:
                time.sleep(backoff_time)
                backoff_time *= 2
    return text


def xml_to_data(xml_text):
    root = ElementTree.fromstring(xml_text)
    
    games_data = []
    for game in root:
        # print(game.tag)
        game_data = {
            'playerCounts': [
                { 'supported': False, 'recommended': False, 'best': False },
                { 'supported': False, 'recommended': False, 'best': False },
                { 'supported': False, 'recommended': False, 'best': False },
                { 'supported': False, 'recommended': False, 'best': False },
                { 'supported': False, 'recommended': False, 'best': False },
                { 'supported': False, 'recommended': False, 'best': False },
                { 'supported': False, 'recommended': False, 'best': False },
                { 'supported': False, 'recommended': False, 'best': False },
                { 'supported': False, 'recommended': False, 'best': False },
                { 'supported': False, 'recommended': False, 'best': False }
            ],
            'supportedMin': 0,
            'supportedMax': 0
        };

        for element in game:

            if element.tag == 'name' and element.attrib['type'] == 'primary':
                game_data['name'] = element.attrib['value']

            if element.tag == 'thumbnail':
                game_data['thumbnail'] = element.text
            
            if element.tag == 'minplayers':
                game_data['supportedMin'] = int(element.attrib['value'])

            if element.tag == 'maxplayers':
                game_data['supportedMax'] = int(element.attrib['value'])
            
            if element.tag == 'poll' and element.attrib['name'] == 'suggested_numplayers':
                for count in element:
                    if count.attrib['numplayers'].endswith('+'): continue
                    if int(count.attrib['numplayers']) > 10: continue

                    best_votes = 0
                    rec_votes = 0
                    notrec_votes = 0

                    for poll_result in count:
                        if poll_result.attrib['value'] == 'Best':
                            best_votes = int(poll_result.attrib['numvotes'])
                        if poll_result.attrib['value'] == 'Recommended':
                            rec_votes = int(poll_result.attrib['numvotes'])
                        if poll_result.attrib['value'] == 'Not Recommended':
                            notrec_votes = int(poll_result.attrib['numvotes'])

                    game_data['playerCounts'][int(count.attrib['numplayers']) - 1] = {
                        'recommended': rec_votes + best_votes > notrec_votes,
                        'best': best_votes > rec_votes and rec_votes + best_votes > notrec_votes,
                        'supported': False
                    }

            if element.tag == 'statistics':
                for statistic in element:
                    if statistic.tag == 'average':
                        game_data['rating'] = float(statistic.attrib['value'])
            
        for i in range(game_data['supportedMin'], game_data['supportedMax']+1):
            if i > 10: break
            game_data['playerCounts'][i-1]['supported'] = True

        games_data.append(game_data)
    
    return games_data


def lambda_handler(event, context):

    game_ids = []

    if event.get('queryStringParameters', False) and 'username' in event['queryStringParameters']:
        username = event['queryStringParameters']['username']
        text = get_backoff(f'https://boardgamegeek.com/xmlapi2/collection?username={username}&own=1')
        user_games = ElementTree.fromstring(text)
        game_ids = list(map(lambda x: x.attrib['objectid'], user_games))
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('Username required'),
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            }
        }
    
    text = get_backoff(f'https://boardgamegeek.com/xmlapi2/thing?type=boardgame&stats=1&id=' + ','.join(game_ids))
    games_data = xml_to_data(text)

    return {
        'statusCode': 200,
        'body': json.dumps(games_data),
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        }
    }


if __name__ == '__main__':
    if len(sys.argv) > 1:
        event = {
            'queryStringParameters': {
                'username': sys.argv[1]
            }
        }
    else:
        event = {}
    
    print(lambda_handler(event, {})['body'])