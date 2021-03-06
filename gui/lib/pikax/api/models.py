import datetime
import enum
import os
from multiprocessing.dummy import Pool
from typing import List, Tuple, Union, Type, Any

import texts
from .. import params, util
from ..exceptions import ArtworkError


class APIUserInterface:

    def bookmarks(self, limit: int = None, bookmark_type: params.BookmarkType = params.BookmarkType.ILLUST_OR_MANGA,
                  restrict: params.Restrict = params.Restrict.PUBLIC) -> List[int]:
        raise NotImplementedError

    def illusts(self, limit: int = None) -> List[int]: raise NotImplementedError

    def mangas(self, limit: int = None) -> List[int]: raise NotImplementedError

    @property
    def id(self): raise NotImplementedError

    @property
    def name(self): raise NotImplementedError

    @property
    def account(self): raise NotImplementedError


class APIAccessInterface:
    def visits(self, user_id: int) -> APIUserInterface:
        raise NotImplementedError


class APIPagesInterface:

    def search(self, keyword: str = '',
               search_type: params.Type = params.Type.ILLUST,
               match: params.Match = params.Match.PARTIAL,
               sort: params.Sort = params.Sort.DATE_DESC,
               search_range: Union[datetime.timedelta, params.Range] = None,
               limit: int = None) -> List[int]: raise NotImplementedError

    def rank(self,
             rank_type: params.RankType = params.RankType.DAILY,
             content: params.Content = params.Content.ILLUST,
             date: Union[str, datetime.date] = format(datetime.date.today(), '%Y%m%d'),
             limit: int = None) -> List[int]: raise NotImplementedError


class Artwork:

    def __init__(self, artwork_id):
        self.id = artwork_id
        self.config()

    @property
    def bookmarks(self): raise NotImplementedError

    @property
    def views(self): raise NotImplementedError

    @property
    def author(self): raise NotImplementedError

    @property
    def title(self): raise NotImplementedError

    @property
    def likes(self): raise NotImplementedError

    class DownloadStatus(enum.Enum):
        OK = texts.get('DOWNLOAD_STATUS_OK')
        SKIPPED = texts.get('DOWNLOAD_STATUS_SKIPPED')
        FAILED = texts.get('DOWNLOAD_STATUS_FAILED')

    # return download status, content, filename
    def __getitem__(self, index) -> Tuple[DownloadStatus, Any, str]: raise NotImplementedError

    # return num of pages
    def __len__(self): raise NotImplementedError

    # set variables, raises ReqException if fails
    def config(self):
        raise NotImplementedError


class BaseIDProcessor:

    def __init__(self):
        self.type_to_function = {
            params.ProcessType.MANGA: self.process_mangas,
            params.ProcessType.ILLUST: self.process_illusts,
        }

    def process_illusts(self, ids: List[int]) -> Tuple[List[Artwork], List[int]]:
        raise NotImplementedError

    def process_mangas(self, ids: List[int]) -> Tuple[List[Artwork], List[int]]:
        raise NotImplementedError

    def process(self, ids: List[int], process_type: params.ProcessType) -> Tuple[List[Artwork], List[int]]:
        if not params.ProcessType.is_valid(process_type):
            from ..exceptions import ProcessError
            raise ProcessError(texts.get('PROCESS_TYPE_ERROR').format(process_type=process_type, process_class=params.ProcessType))

        return self.type_to_function[process_type](ids)

    @staticmethod  # param cls is pass in as argument
    def _general_processor(cls: Type[Artwork], item_ids: List[int]) -> Tuple[List[Artwork], List[int]]:
        util.log(texts.get('PROCESS_ID_INITIALIZING'), start=os.linesep, inform=True)
        total = len(item_ids)
        successes = []
        fails = []
        pool = Pool(os.cpu_count())

        def process_item(itemid):
            try:
                successes.append(cls(itemid))
            except ArtworkError:
                fails.append(itemid)

        for index, item_id in enumerate(pool.imap_unordered(process_item, item_ids)):
            util.print_progress(index + 1, total, title=texts.get('PROCESS_ID_TITLE'))
        msg = texts.get('PROCESS_FINISHED_MESSAGE').format(total=total, successes=len(successes), fails=len(fails))
        util.print_done(msg)
        return successes, fails
