/*
 * Display of the list of pairs of questions and answers.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

import SearchQuestion from "arxifter/biorxiv/searchquestion.js";
import SearchWaiting from "arxifter/biorxiv/searchwaiting.js";
import SearchAnswer from "arxifter/biorxiv/searchanswer.js";

class SearchList extends React.Component {
    constructor(props) {
        super(props);
        {
            const iniSearchList = props.searchList ?? [];
            this.state = {
                toSaveLastSearches: props.getSaveLastSearches(),
                searchList: iniSearchList,
                // the same value of rankForSearchID can be used
                // for making a search ID of two different searches
                // if the searches do not come in the same ms
                // (even within-ms IDs should end up being different);
                // thus doing it in a way that requires a page reload
                // to have a possibility for such a situation,
                // since expecting that the combination of user action
                // within the UI and page reload takes more time;
                rankForSearchID: iniSearchList.length,
                waitingTimestamp: 0,
                waiting: false
            };
        }
        this.startWaiting = () => {
            this.setState({
                waiting: true
            });
            setTimeout(this.updateWaiting, 1000);
        };
        this.updateWaiting = () => {
            if (!this.state.waiting) {
                return;
            }
            this.setState({
                waitingTimestamp: Date.now()
            });
            setTimeout(this.updateWaiting, 1000);
        };
        this.stopWaiting = () => {
            this.setState({
                waiting: false
            });
        };
        this.getToSaveLastSearches = () => {
            return this.state.toSaveLastSearches;
        };
        this.setToSaveLastSearches = (doSaving) => {
            this.setState({
                toSaveLastSearches: doSaving
            });
        };
        this.getSearchList = () => {
            return this.state.searchList;
        };
        this.getFeedDesc = (feedDesc) => {
            if (!utilsIsString(feedDesc)) {
                return "the feed articles";
            }
            return feedDesc;
        }
        this.sortArticleData = (article) => {
            if (!utilsIsDict(article)) {
                return article;
            }
            let sortedArticle = {};
            let usedKeys = [];

            const keySuggestion = utilsGetKey(
                article, utilsGetSuggestionKey()
            );
            if (keySuggestion !== null) {
                sortedArticle["matches"] = !(article[keySuggestion]);
                usedKeys.push(keySuggestion);
            }
            const keySubject = utilsGetKey(
                article, utilsGetSubjectKey()
            );
            if (keySubject !== null) {
                sortedArticle["subject"] = (
                    article[keySubject].replaceAll("_", " ")
                );
                usedKeys.push(keySubject);
            }

            const baseKeys = [
                "title",
                "date",
                "version",
                "type",
                "doi",
                "link",
                "authors",
                "abstract"
            ];
            baseKeys.forEach((key, idx) => {
                const realKey = utilsGetKey(article, key);
                if (realKey !== null) {
                    sortedArticle[key] = article[realKey];
                    usedKeys.push(realKey);
                }
            })

            Object.entries(article).map(([key, val]) => {
                if (!(usedKeys.includes(key))) {
                    sortedArticle[key] = val;
                }
            });
            return sortedArticle;
        };
        this.canUseFileAPI = () => {
            if (!("showSaveFilePicker" in window)) {
                return false;
            }
            try {
                if (window.self !== window.top) {
                    return false;
                }
            } catch (e) {
                return false;
            }
            return true;
        };
        this.suggestFileName = (item, rank) => {
            const timestamp = item?.timestamp ?? 0;
            let ts = Number(timestamp);
            if (!isFinite(ts)) {
                ts = 0;
            } else {
                ts = Math.max(0, Math.round(ts));
            }
            if (!ts) {
                return `sifting_${rank}.json`;
            }
            const dt = new Date(ts);
            const tsFormatted = (
                dt.getFullYear()
                + "-"
                + String(dt.getMonth() + 1).padStart(2, 0)
                + "-"
                + String(dt.getDate()).padStart(2, 0)
                + "_"
                + String(dt.getHours()).padStart(2, 0)
                + "-"
                + String(dt.getMinutes()).padStart(2, 0)
                + "-"
                + String(dt.getSeconds()).padStart(2, 0)
            );
            return `sifting_${tsFormatted}.json`;
        };
        this.downloadSearchClassic = (downloadBlob, downloadItem, rank) => {
            const downloadElem = document.createElement("a");
            const url = URL.createObjectURL(downloadBlob);
            document.body.appendChild(downloadElem);
            downloadElem.href = url;
            downloadElem.download = this.suggestFileName(downloadItem, rank);
            downloadElem.click();
            downloadElem.remove();
            window.URL.revokeObjectURL(url);
        };
        this.downloadSearch = async (id, rank) => {
            let downloadItem = {};
            this.state.searchList.forEach((item) => {
                if (item.id == id) {
                    downloadItem = item;
                }
            });
            try {
                const downloadBlob = new Blob([JSON.stringify({
                    "subjects": downloadItem?.question?.subject,
                    "query": downloadItem?.question?.query,
                    "sifted": this.getFeedDesc(downloadItem?.question?.feed),
                    "answer": downloadItem?.answers?.flat().map(
                        item => this.sortArticleData(item)
                    )
                }, null, 4)], {type: "application/json"});
                if (!this.canUseFileAPI()) {
                    this.downloadSearchClassic(
                        downloadBlob, downloadItem, rank
                    );
                    return;
                }
                const newHandle = await window.showSaveFilePicker({
                    id: "arxifter-biorxiv-sifting-result",
                    suggestedName: this.suggestFileName(downloadItem, rank),
                    types: [{
                        description: "JSON files",
                        accept: {"application/json": [".json"]}
                    }]
                });
                const writableStream = await newHandle.createWritable();
                await writableStream.write(downloadBlob);
                await writableStream.close();
            } catch (e) {}
        };
        this.removeSearch = (id) => {
            let searchList = [];
            this.state.searchList.forEach((item) => {
                if (item.id != id) {
                    searchList.push(item)
                }
            });
            this.setState({
                searchList: searchList
            })
            // it is necessary to provide the list here,
            // b/c its form in this.state.searchList
            // has the updated value only after re-rendering
            this.saveLastSearches(null, searchList);
        };
        this.saveLastSearches = (toSave, searchList) => {
            if (toSave ?? this.getToSaveLastSearches()) {
                storageSaveSifts(
                    props.getStoragePrefix(),
                    searchList ?? this.state.searchList,
                    getFabricUi()["recallSifts"]
                );
            } else {
                storageCleanSifts(
                    props.getStoragePrefix()
                );
            }
        };
        this.addSearch = (isAnswer, content) => {
            // a single answer should come to any question,
            // and any answer should have a previous question,
            // but better to take it more dynamically;
            let searchList = this.state.searchList;
            const rankForSearchID = this.state.rankForSearchID;
            this.setState({
                // this value is generally not the rank of the item;
                rankForSearchID: rankForSearchID + 1
            });
            if (!isAnswer) {
                // a new question was made;
                searchList.push({
                    id: utilsGenSearchID(rankForSearchID),
                    question: content,
                    timestamp: Date.now(),
                    answers: []
                });
                this.setState({
                    searchList: searchList
                });
                this.startWaiting();
                return;
            }
            this.stopWaiting();
            // if here, it is an answer;
            if (searchList.length == 0) {
                // if here, there is no previous question though;
                // this situation should not happen,
                // but better to take care about it too;
                searchList.push({
                    id: utilsGenSearchID(rankForSearchID),
                    question: {subject: "---", query: ""},
                    answers: [content]
                });
                this.setState({
                    searchList: searchList
                });
                return;
            }
            // adding an answer to a question;
            // it should always be with a single answer,
            // but doing it more generally;
            let lastQA = searchList.pop();
            lastQA.answers.push(content);
            searchList.push(lastQA);
            this.setState({ searchList: searchList });
        };
    }

    render() {
        const searchCount = this.state.searchList.length;
        return (
            <div id="search-list">
                {
                    this.state.searchList.slice().reverse().map((x, i) => (
                    <div
                        key={x.id}
                    >
                        {
                            (i > 0) &&
                            <hr
                                key={`s_${x.id}`}
                                className="search-separator"
                            />
                        }
                        {
                            (x.question !== null) &&
                            <SearchQuestion
                                key={`q_${x.id}`}
                                rank={searchCount - i}
                                content={x.question}
                                timestamp={x.timestamp ?? 0}
                                doSave={() => this.downloadSearch(
                                    x.id,
                                    searchCount - i
                                )}
                                doRemoval={() => this.removeSearch(x.id)}
                                actionActive={x.answers.length > 0}
                            />
                        }
                        {
                            ((i == 0) && (x.answers.length == 0)) &&
                            <SearchWaiting
                                key={`w_${x.id}`}
                                timestamp={x.timestamp}
                            />
                        }
                        {
                            x.answers.map((y, j) => (
                                <SearchAnswer
                                    key={`a_${x.id}_${j}`}
                                    content={y}
                                />
                            ))
                        }
                    </div>
                    ))
                }
            </div>
        );
    }
}

export { SearchList as default };
