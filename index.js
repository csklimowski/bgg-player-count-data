
const fetch = require('node-fetch');
const xml2json = require('xml2json');
// const AWS = require('aws-sdk');
// const ddb = new AWS.DynamoDB.DocumentClient();

function arr(item) {
    return item instanceof Array ? item : [item];
}

exports.handler = async (event) => {

    let username = event.queryStringParameters.username;

    let gameIds = [];

    try {
        if (username) {
            let res = await fetch('https://boardgamegeek.com/xmlapi2/collection?username=' + username + '&own=1')
            let textRes = await res.text();
            let data = JSON.parse(xml2json.toJson(textRes));

            gameIds = arr(data.items.item).map(g => g.objectid);

        } else {
            let res = await fetch('https://boardgamegeek.com/browse/boardgame');
            let textRes = await res.text();
            let re = /boardgame\/(\d+)\//g;
            let match;
            do {
                match = re.exec(textRes);
                if (match) {
                    if (gameIds[gameIds.length-1] !== match[1]) {
                        gameIds.push(match[1]);
                    }
                }
            } while (match);
        }
    } catch(err) {
        console.log(err);
        return {
            statusCode: 500,
            body: 'An error occurred.'
        };
    }

    let gameStats = [];

    try {
        let res = await fetch('https://boardgamegeek.com/xmlapi2/thing?type=boardgame&stats=1&id=' + gameIds.join(','));
        let textRes = await res.text();
        let data = JSON.parse(xml2json.toJson(textRes));
        
        for (let game of arr(data.items.item)) {
            let gameData = {
                playerCounts: [
                    { supported: false, recommended: false, best: false },
                    { supported: false, recommended: false, best: false },
                    { supported: false, recommended: false, best: false },
                    { supported: false, recommended: false, best: false },
                    { supported: false, recommended: false, best: false },
                    { supported: false, recommended: false, best: false },
                    { supported: false, recommended: false, best: false },
                    { supported: false, recommended: false, best: false },
                    { supported: false, recommended: false, best: false },
                    { supported: false, recommended: false, best: false }
                ],
                supportedMin: parseInt(game.minplayers.value),
                supportedMax: parseInt(game.maxplayers.value),
                rating: parseFloat(game.statistics.ratings.average.value),
                thumbnail: game.thumbnail
            };

            for (let name of arr(game.name)) {
                if (name.type === 'primary') gameData.name = name.value;
            }

            for (let poll of arr(game.poll)) {
                if (poll.name === 'suggested_numplayers') {
                    for (let count of arr(poll.results)) {
                        if (/\+$/.test(count.numplayers)) continue;

                        let bestVotes = 0;
                        let recVotes = 0;
                        let notRecVotes = 0;

                        for (let pollResult of arr(count.result)) {
                            if (pollResult.value === 'Best')
                                bestVotes = parseInt(pollResult.numvotes);
                            if (pollResult.value === 'Recommended')
                                recVotes = parseInt(pollResult.numvotes);
                            if (pollResult.value === 'Not Recommended')
                                notRecVotes = parseInt(pollResult.numvotes);
                        }

                        let countData = gameData.playerCounts[parseInt(count.numplayers) - 1];
                        if (countData) {
                            countData.recommended = recVotes + bestVotes >= notRecVotes;
                            countData.best = bestVotes >= recVotes && recVotes + bestVotes > notRecVotes;
                        }
                    }
                }
            }

            for (let i = gameData.supportedMin; i < gameData.supportedMax+1 && i < 11; i++) {
                gameData.playerCounts[i-1].supported = true;
            }

            gameStats.push(gameData);
        }
    } catch(err) {
        console.log(err);
        return {
            statusCode: 500,
            body: 'An error occurred.'
        };
    }

    return {
        statusCode: 200,
        body: JSON.stringify(gameStats)
    };
};


    
//     // ddb.get({
//     //     TableName: 'bggData',
//     //     Key: username
//     // }, (err, data) => {
//     //     if (err) console.log(err);
//     //     else console.log(data);
//     // });
    
    
//     // ddb.put({
//     //     Item: {
//     //         username: 'csklimowski'
//     //     }
//     // })
// };
